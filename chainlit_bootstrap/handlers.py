"""Chainlit event handlers."""

import asyncio
import logging
import random
import uuid

import chromadb
from llama_index.core import Document, VectorStoreIndex
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.vector_stores.chroma import ChromaVectorStore

import chainlit as cl

from .assistants import AssistantDescriptor, discover_assistants
from .atc_parser import parse_atc_conversation
from .audio import is_audio_file, transcribe_audio
from .charts import histogram_from_values
from .llm import embeddings, llm, text_splitter
from .search import (
    TavilyNotConfiguredError,
    is_web_search_configured,
    run_web_search,
)

logger = logging.getLogger(__name__)

# Initialize assistant registry at module level
_assistant_registry = discover_assistants()


def _format_parsed_conversation(parsed_conversation: list) -> str:
    """
    Format parsed ATC conversation into readable markdown format (without bullets).

    Args:
        parsed_conversation: List of dicts with 'role' and 'message' keys

    Returns:
        Formatted markdown string (non-bulleted format for fallback)
    """
    if not parsed_conversation:
        return ""

    formatted_lines = []
    for item in parsed_conversation:
        role = item.get("role", "unknown").upper()
        message = item.get("message", "")
        # Use bold for role labels, but no bullets (for fallback display)
        formatted_lines.append(f"**{role}**: {message}")

    return "\n\n".join(formatted_lines)


async def _process_audio_file(file: cl.File) -> bool:
    """
    Process an uploaded audio file by transcribing it with OpenAI Whisper API
    and parsing it into structured ATC conversation format.

    Args:
        file: Chainlit File object representing the uploaded audio file

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Starting audio processing for file: {file.name}, path: {file.path}")
    progress_msg = cl.Message(content=f"🎤 Processing audio file `{file.name}`...")
    await progress_msg.send()

    try:
        # Step 1: Transcribe the audio file (wrap sync function in async)
        logger.info(f"Calling transcribe_audio for {file.path}")
        result = await cl.make_async(transcribe_audio)(file.path, file.name)
        transcription_text = result["transcription"]
        logger.info(f"Transcription successful: {len(transcription_text)} characters")

        # Step 2: Parse the transcript into structured conversation
        parsed_conversation = None
        parsing_error = None
        try:
            logger.info("Parsing transcript into ATC conversation format")
            parsed_conversation = await cl.make_async(parse_atc_conversation)(transcription_text)
            logger.info(f"Successfully parsed {len(parsed_conversation)} conversation messages")
        except Exception as e:
            logger.warning(f"Failed to parse ATC conversation: {e}")
            parsing_error = str(e)
            # Continue even if parsing fails - we'll still show the raw transcript

        # Create audio element for playback
        audio_element = cl.Audio(
            path=result["audio_path"],
            name=file.name,
            display="inline",
        )

        # Build response content with collapsible transcript and parsed conversation
        response_parts = []

        # Audio player section
        response_parts.append("🎤 **Audio Transcription Complete**\n")

        # Prepare elements list
        elements = [audio_element]

        # Parsed conversation section (show this prominently using custom element)
        if parsed_conversation:
            response_parts.append("#### ATC Dialog\n")
            # Create custom conversation view element as primary display method
            logger.info(f"Creating ConversationView element with {len(parsed_conversation)} messages")
            conversation_element = cl.CustomElement(
                name="ConversationView",
                props={
                    "conversation": parsed_conversation
                }
            )
            elements.append(conversation_element)
            logger.info(f"Added ConversationView element to elements list. Total elements: {len(elements)}")
            # Add fallback text so content renders even if custom element fails
            # This is the formatted conversation without bullets - it was what you saw before
            fallback_text = _format_parsed_conversation(parsed_conversation)
            if fallback_text:
                response_parts.append(fallback_text)
        elif parsing_error:
            response_parts.append(
                f"#### ATC Dialog\n"
                f"⚠️ Failed to parse conversation: {parsing_error}\n"
            )
        else:
            response_parts.append(
                "#### ATC Dialog\n"
                "⚠️ Could not parse conversation.\n"
            )

        response_content = "\n".join(response_parts)
        
        # Create collapsible section custom element for raw transcript
        transcript_content = str(transcription_text) if transcription_text else ""
        logger.info(f"Creating collapsible element with content length: {len(transcript_content)}")
        
        collapsible_element = cl.CustomElement(
            name="CollapsibleSection",
            props={
                "title": "Raw Transcript",
                "content": transcript_content
            }
        )
        elements.append(collapsible_element)

        # Prepare metadata
        metadata = {
            "transcription": transcription_text,
            "audio_path": result["audio_path"],
            "audio_format": result["format"],
            "original_filename": result["original_filename"],
        }
        if parsed_conversation:
            metadata["parsed_conversation"] = parsed_conversation

        response_msg = cl.Message(
            content=response_content,
            elements=elements,
            metadata=metadata,
        )
        await response_msg.send()

        progress_msg.content = f"✅ Audio file `{file.name}` transcribed and parsed successfully!"
        await progress_msg.update()

        return True

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Failed to process audio file {file.name}: {e}\n{error_trace}")
        error_msg = (
            f"❌ Failed to transcribe audio file `{file.name}`: {str(e)}\n\n"
            "Please ensure:\n"
            "- The file is a valid audio format (.mp3, .wav, .m4a)\n"
            "- The file is not corrupted\n"
            "- OpenAI API key is configured correctly\n\n"
            f"Error details: {type(e).__name__}"
        )
        progress_msg.content = error_msg
        await progress_msg.update()
        return False


async def _process_file(file: cl.File) -> bool:
    """
    Process an uploaded file and set up the vector store index.

    Currently only text files are supported. PDF support requires additional libraries like pypdf.
    Returns True if successful.
    """
    msg = cl.Message(content=f"Processing `{file.name}`...")
    await msg.send()

    try:
        with open(file.path, encoding="utf-8") as f:
            text = f.read()
        if not text.strip():
            await cl.Message(
                content=f"Error: File `{file.name}` is empty. Please upload a file with content."
            ).send()
            return False
    except UnicodeDecodeError:
        await cl.Message(
            content=f"Error: Could not read file `{file.name}`. Please ensure it's a text file."
        ).send()
        return False
    except Exception as e:
        await cl.Message(
            content=f"Error: Failed to read file `{file.name}`: {str(e)}"
        ).send()
        return False

    # Create LlamaIndex Document
    document = Document(text=text, metadata={"source": file.name})

    # Create ChromaDB collection for this session
    chroma_client = chromadb.Client()
    collection_name = f"session_{uuid.uuid4().hex[:8]}"
    chroma_collection = chroma_client.get_or_create_collection(name=collection_name)

    # Create vector store and index
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_documents(
        [document],
        vector_store=vector_store,
        embed_model=embeddings,
        transformations=[text_splitter],
    )

    msg.content = f"Processing `{file.name}` done. You can now ask questions!"
    await msg.update()

    cl.user_session.set("index", index)
    cl.user_session.set("file_name", file.name)
    return True


def _get_general_memory() -> ChatMemoryBuffer:
    """Return or initialize the general chat memory for the session."""
    memory: ChatMemoryBuffer | None = cl.user_session.get("general_memory")
    if memory is None:
        memory = ChatMemoryBuffer.from_defaults(token_limit=3000)
        cl.user_session.set("general_memory", memory)
    return memory


async def _respond_with_general_chat(user_input: str) -> None:
    """Provide a response using the base LLM when no document is loaded."""
    if not user_input.strip():
        await cl.Message(
            content="Please enter a question or upload a document to get started."
        ).send()
        return

    memory = _get_general_memory()
    
    # Create a simple chat engine with memory
    from llama_index.core.chat_engine import SimpleChatEngine
    
    chat_engine = SimpleChatEngine.from_defaults(
        llm=llm,
        memory=memory,
    )
    
    # Stream the response
    response = cl.Message(content="")
    await response.send()
    
    # Use stream_chat() wrapped in make_async since astream_chat() 
    # returns a coroutine instead of an async iterator for SimpleChatEngine
    # We need to run the synchronous generator iteration in a thread to avoid blocking
    full_response = ""
    
    def _collect_tokens():
        """Collect all tokens from the stream in a thread."""
        tokens = []
        for token in chat_engine.stream_chat(user_input):
            tokens.append(token)
        return tokens
    
    tokens = await asyncio.to_thread(_collect_tokens)
    
    # Stream the collected tokens asynchronously with throttling
    # Update every few tokens to avoid "Too many packets in payload" error
    update_interval = 5  # Update every 5 tokens
    for idx, token in enumerate(tokens):
        if hasattr(token, 'delta'):
            full_response += token.delta
        elif hasattr(token, 'response'):
            # If token has a response attribute, use it
            full_response = str(token.response)
        else:
            full_response += str(token)
        
        # Only update periodically to avoid overwhelming WebSocket
        if (idx + 1) % update_interval == 0 or idx == len(tokens) - 1:
            response.content = full_response
            await response.update()
            # Small delay to prevent overwhelming the WebSocket
            await asyncio.sleep(0.01)
    
    # Final update to ensure complete response is shown
    if full_response:
        response.content = full_response
        await response.update()


def _parse_assistant_command(user_input: str) -> tuple[str | None, str]:
    """
    Parse assistant-related commands from user input.
    
    Returns:
        Tuple of (command_type, remainder) where:
        - command_type: "list", "switch", "direct", or None
        - remainder: remaining text after command
    """
    if not user_input:
        return None, ""
    
    trimmed = user_input.strip()
    lower_trimmed = trimmed.lower()
    
    # /assistant list
    if lower_trimmed == "/assistant list" or lower_trimmed.startswith("/assistant list "):
        return "list", ""
    
    # /assistant <name>
    if lower_trimmed.startswith("/assistant "):
        parts = trimmed.split(maxsplit=2)
        if len(parts) >= 2:
            assistant_name = parts[1]
            return "switch", assistant_name
        return "switch", ""
    
    # /<command> <message> - direct assistant command
    if trimmed.startswith("/"):
        parts = trimmed.split(maxsplit=1)
        command = parts[0][1:]  # Remove leading /
        assistant = _assistant_registry.get(command)
        if assistant:
            remainder = parts[1] if len(parts) > 1 else ""
            return "direct", f"{command} {remainder}".strip()
    
    return None, trimmed


def _extract_search_query(user_input: str) -> str | None:
    """Return the search query if the user prefixed their message with a search command."""
    if not user_input:
        return None

    trimmed = user_input.strip()
    lower_trimmed = trimmed.lower()

    if lower_trimmed.startswith("/search"):
        parts = trimmed.split(maxsplit=1)
        return parts[1].strip() if len(parts) > 1 else ""
    if lower_trimmed.startswith("!search"):
        parts = trimmed.split(maxsplit=1)
        return parts[1].strip() if len(parts) > 1 else ""
    for prefix in ("search:", "web:", "lookup:"):
        if lower_trimmed.startswith(prefix):
            return trimmed[len(prefix) :].strip()

    return None


def _parse_chart_request(user_input: str) -> int | None:
    """Return the requested sample size if the user issued a /chart command."""
    if not user_input:
        return None

    trimmed = user_input.strip()
    if not trimmed.lower().startswith("/chart"):
        return None

    parts = trimmed.split()
    if len(parts) == 1:
        return 200

    try:
        requested = int(parts[1])
    except ValueError:
        return 200

    return max(20, min(2000, requested))


async def _respond_with_demo_chart(sample_size: int) -> None:
    """Render a Seaborn histogram and return it as a Chainlit attachment."""
    rng = random.Random(sample_size)
    values = [rng.gauss(mu=0, sigma=1) for _ in range(sample_size)]

    chart = histogram_from_values(
        values, title=f"Demo distribution (n={sample_size})"
    )

    await cl.Message(
        content=(
            "📊 Here's a Seaborn-powered histogram rendered in Chainlit.\n"
            "Use `/chart <sample_size>` to choose between 20 and 2000 points."
        ),
        elements=[chart],
    ).send()


async def _respond_with_web_search(query: str) -> None:
    """Execute a Tavily web search and stream the results back to the user."""
    if not query:
        await cl.Message(
            content="Please provide a query after the `/search` command. Example: `/search latest Chainlit release`"
        ).send()
        return

    progress = cl.Message(content=f"🔎 Searching the web for `{query}`...")
    await progress.send()

    try:
        results = await cl.make_async(run_web_search)(query)
    except TavilyNotConfiguredError:
        progress.content = (
            "⚠️ Web search is not configured. "
            "Set the `TAVILY_API_KEY` environment variable and restart the app."
        )
        await progress.update()
        return
    except Exception as exc:  # noqa: BLE001
        progress.content = f"❌ Web search failed: {type(exc).__name__}: {exc}"
        await progress.update()
        return

    if not results:
        progress.content = f"🔎 No web results found for `{query}`."
        await progress.update()
        return

    formatted_results = []
    for idx, result in enumerate(results, start=1):
        title = result.get("title") or "Untitled result"
        url = result.get("url") or ""
        snippet = result.get("content") or result.get("snippet") or ""
        if url:
            formatted_results.append(
                f"{idx}. **[{title}]({url})**\n{snippet}".strip()
            )
        else:
            formatted_results.append(f"{idx}. **{title}**\n{snippet}".strip())

    progress.content = "🔎 **Web search results:**\n\n" + "\n\n".join(
        formatted_results
    )
    await progress.update()


@cl.on_chat_start
async def on_chat_start():
    """Initialize chat session and ensure database is initialized."""
    # Log audio config state for debugging (config should already be set via TOML)
    try:
        import chainlit.config as cfg
        if hasattr(cfg.config, 'features') and hasattr(cfg.config.features, 'audio'):
            audio_enabled = cfg.config.features.audio.enabled
            logger.info(f"Audio feature config state: enabled={audio_enabled}")
            if not audio_enabled:
                logger.warning(
                    "Audio feature is disabled in config. "
                    "Check chainlit.toml [features.audio] enabled setting."
                )
    except Exception as e:
        logger.debug(f"Could not check audio config in on_chat_start: {e}")
    
    # Trigger database initialization to ensure tables exist before Chainlit queries them
    try:
        data_layer = cl.data_layer
        if data_layer:
            try:
                await data_layer.list_threads(user_id="__init__", pagination=None, filters=None)
            except Exception:
                # Tables will be created on next access if this fails (expected on first run)
                pass
    except Exception:
        # Database will be initialized when actually needed
        pass

    index = cl.user_session.get("index")
    if index:
        file_name = cl.user_session.get("file_name", "document")
        await cl.Message(
            content=f"👋 Welcome back! You can continue asking questions about `{file_name}`."
        ).send()
        return

    # Set default assistant (first registered or None)
    assistants = _assistant_registry.list_all()
    if assistants:
        default_assistant = assistants[0]
        cl.user_session.set("active_assistant", default_assistant.command)
    else:
        cl.user_session.set("active_assistant", None)

    welcome_message = (
        "👋 Welcome! You can start chatting right away, upload a text file (📎) "
        "if you want me to answer questions about that document, or upload an audio file "
        "(.mp3, .wav, .m4a) to get it transcribed automatically."
    )
    
    # Add assistant information
    if assistants:
        assistant_list = "\n".join(
            f"- `/{a.command}`: {a.name} - {a.description}" for a in assistants
        )
        welcome_message += (
            f"\n\n**Available Assistants:**\n{assistant_list}\n\n"
            "Use `/assistant <name>` to switch assistants, or `/<command> <message>` "
            "to use a specific assistant directly."
        )
    
    if is_web_search_configured():
        welcome_message += (
            "\n\nNeed the latest info? Type `/search your question` to run a live Tavily web search."
        )
    welcome_message += (
        "\n\nWant a visual? Type `/chart 200` (or another size) to see a Seaborn histogram."
    )

    await cl.Message(content=welcome_message).send()


async def _process_audio_element(audio_element: cl.Audio) -> bool:
    """
    Process an Audio element by transcribing it with OpenAI Whisper API.
    
    Args:
        audio_element: Chainlit Audio element
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Processing Audio element: name={audio_element.name}, path={audio_element.path}")
    
    # Create a temporary File-like object for compatibility with _process_audio_file
    # We'll pass the path and name directly to transcribe_audio
    class AudioFileWrapper:
        def __init__(self, audio_elem: cl.Audio):
            self.name = audio_elem.name
            self.path = audio_elem.path
            self.mime = audio_elem.mime or ""
    
    file_wrapper = AudioFileWrapper(audio_element)
    return await _process_audio_file(file_wrapper)


@cl.on_message
async def main(message: cl.Message):
    """Handle incoming messages and document QA."""
    # Handle file uploads if present
    if message.elements:
        audio_processed = False
        logger.info(f"Message has {len(message.elements)} elements")
        for element in message.elements:
            logger.info(f"Element type: {type(element).__name__}, element: {element}")
            
            # Check for Audio elements first (Chainlit creates these for audio uploads)
            if isinstance(element, cl.Audio):
                logger.info(f"Audio element detected: name={element.name}, path={element.path}, mime={element.mime}")
                try:
                    success = await _process_audio_element(element)
                    logger.info(f"Audio processing result: success={success}")
                    audio_processed = True
                    # If no text content with audio file, return early
                    if not message.content or not message.content.strip():
                        logger.info("No text content, returning early after audio processing")
                        return
                    # Continue processing text content if present
                    break
                except Exception as e:
                    logger.error(f"Exception during audio processing: {e}", exc_info=True)
                    # Still mark as processed to prevent fallthrough
                    audio_processed = True
                    if not message.content or not message.content.strip():
                        return
                    break
            
            elif isinstance(element, cl.File):
                # Check if it's an audio file first
                is_audio = is_audio_file(element.mime or "", element.name)
                logger.info(
                    f"File detected: name={element.name}, mime={element.mime}, "
                    f"is_audio={is_audio}, path={element.path}"
                )
                if is_audio:
                    try:
                        success = await _process_audio_file(element)
                        logger.info(f"Audio processing result: success={success}")
                        audio_processed = True
                        # If no text content with audio file, return early
                        if not message.content or not message.content.strip():
                            logger.info("No text content, returning early after audio processing")
                            return
                        # Continue processing text content if present
                        break
                    except Exception as e:
                        logger.error(f"Exception during audio processing: {e}", exc_info=True)
                        # Still mark as processed to prevent fallthrough
                        audio_processed = True
                        if not message.content or not message.content.strip():
                            return
                        break
                else:
                    # Process as text file
                    success = await _process_file(element)
                    if success:
                        await cl.Message(
                            content="✅ File processed successfully! You can now ask questions about the document."
                        ).send()
                    else:
                        await cl.Message(
                            content="❌ Failed to process the file. Please ensure it's a valid text file and try again."
                        ).send()

                    # If no text content with file, return early
                    if not message.content or not message.content.strip():
                        return
                    break
        
        # If we processed an audio file and there's no text content, return early
        if audio_processed and (not message.content or not message.content.strip()):
            logger.info("Returning early after audio processing (no text content)")
            return

    user_content = message.content or ""

    # Handle assistant commands
    cmd_type, cmd_remainder = _parse_assistant_command(user_content)
    
    if cmd_type == "list":
        assistants = _assistant_registry.list_all()
        if assistants:
            assistant_list = "\n".join(
                f"- `/{a.command}`: **{a.name}** - {a.description}"
                for a in assistants
            )
            await cl.Message(
                content=f"**Available Assistants:**\n\n{assistant_list}"
            ).send()
        else:
            await cl.Message(content="No assistants are currently registered.").send()
        return
    
    if cmd_type == "switch":
        if not cmd_remainder:
            await cl.Message(
                content="Please specify an assistant name. Use `/assistant list` to see available assistants."
            ).send()
            return
        
        assistant = _assistant_registry.get(cmd_remainder)
        if assistant:
            cl.user_session.set("active_assistant", assistant.command)
            await cl.Message(
                content=f"✅ Switched to **{assistant.name}**. {assistant.description}"
            ).send()
        else:
            await cl.Message(
                content=f"❌ Assistant '{cmd_remainder}' not found. Use `/assistant list` to see available assistants."
            ).send()
        return
    
    if cmd_type == "direct":
        # Extract command and message
        parts = cmd_remainder.split(maxsplit=1)
        command = parts[0]
        assistant_message = parts[1] if len(parts) > 1 else ""
        
        assistant = _assistant_registry.get(command)
        if assistant:
            # Build session context
            context = {
                "user_id": cl.user_session.get("id", "unknown"),
                "file_name": cl.user_session.get("file_name"),
                "index": cl.user_session.get("index"),
            }
            
            # Call assistant handler
            response = await assistant.handle_message(assistant_message, context)
            await cl.Message(content=response).send()
            return

    # Handle shared commands (search, chart) - these work regardless of assistant
    raw_search_query = _extract_search_query(user_content or "")
    if raw_search_query is not None:
        await _respond_with_web_search(raw_search_query)
        return

    chart_sample_size = _parse_chart_request(user_content or "")
    if chart_sample_size is not None:
        await _respond_with_demo_chart(chart_sample_size)
        return

    # Check if active assistant is set and route to it
    active_assistant_cmd = cl.user_session.get("active_assistant")
    if active_assistant_cmd:
        assistant = _assistant_registry.get(active_assistant_cmd)
        if assistant:
            # Build session context
            context = {
                "user_id": cl.user_session.get("id", "unknown"),
                "file_name": cl.user_session.get("file_name"),
                "index": cl.user_session.get("index"),
            }
            
            # Call assistant handler
            response = await assistant.handle_message(user_content, context)
            await cl.Message(content=response).send()
            return

    # Handle document QA if index exists
    index: VectorStoreIndex | None = cl.user_session.get("index")
    if not index:
        await _respond_with_general_chat(user_content)
        return

    # Get or create chat engine with memory
    chat_engine_key = "chat_engine"
    chat_engine = cl.user_session.get(chat_engine_key)
    if chat_engine is None:
        memory = ChatMemoryBuffer.from_defaults(token_limit=3000)
        chat_engine = index.as_chat_engine(
            llm=llm,
            memory=memory,
            similarity_top_k=3,
            streaming=True,
        )
        cl.user_session.set(chat_engine_key, chat_engine)

    # Stream the response
    response = cl.Message(content="")
    await response.send()
    
    full_response = ""
    text_elements: list[cl.Text] = []
    token_count = 0
    
    async for token in chat_engine.astream_chat(user_content):
        if token.delta:
            full_response += token.delta
            token_count += 1
        
        # Extract source nodes if available
        if hasattr(token, "source_nodes") and token.source_nodes:
            for source_idx, node in enumerate(token.source_nodes):
                source_name = f"source_{source_idx}"
                if not any(el.name == source_name for el in text_elements):
                    text_elements.append(
                        cl.Text(
                            content=node.text,
                            name=source_name,
                            display="side",
                        )
                    )
        
        # Throttle updates: update every 5 tokens to avoid "Too many packets" error
        # Also update on first token to show immediate feedback
        update_interval = 5
        if token_count == 1 or token_count % update_interval == 0:
            response.content = full_response
            await response.update()
            # Small delay to prevent overwhelming the WebSocket
            await asyncio.sleep(0.01)
    
    # Final update to ensure complete response is shown
    # (in case the last update didn't happen due to throttling)
    response.content = full_response
    
    # Update response with source elements
    if text_elements:
        source_names = [text_el.name for text_el in text_elements]
        full_response += f"\nSources: {', '.join(source_names)}"
        response.content = full_response
        response.elements = text_elements
    
    await response.update()


@cl.on_audio_chunk
async def on_audio_chunk(audio_chunk):
    """
    Handle real-time audio chunks for voice input.

    TODO: Implement OpenAI Realtime API integration.
    Currently a placeholder that acknowledges audio input.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Audio chunk received: isStart={getattr(audio_chunk, 'isStart', None)}, isEnd={getattr(audio_chunk, 'isEnd', None)}")
    
    if hasattr(audio_chunk, "isStart") and audio_chunk.isStart:
        await cl.Message(content="🎤 Listening...").send()
    elif hasattr(audio_chunk, "isEnd") and audio_chunk.isEnd:
        await cl.Message(
            content="Voice input received. Full OpenAI Realtime API integration coming soon!"
        ).send()
    else:
        # Handle intermediate chunks
        pass
