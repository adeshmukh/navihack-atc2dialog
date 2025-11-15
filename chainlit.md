# Welcome to Chainlit! 🚀🤖

Hi there, Developer! 👋 We're excited to have you on board. Chainlit is a powerful tool designed to help you prototype, debug and share applications built on top of LLMs.

## Useful Links 🔗

- **Documentation:** Get started with our comprehensive [Chainlit Documentation](https://docs.chainlit.io) 📚
- **Discord Community:** Join our friendly [Chainlit Discord](https://discord.gg/k73SQ3FyUh) to ask questions, share your projects, and connect with other developers! 💬

We can't wait to see what you create with Chainlit! Happy coding! 💻😊

## Welcome screen

To modify the welcome screen, edit the `chainlit.md` file at the root of your project. If you do not want a welcome screen, just leave this file empty.

### Tips

- Upload a `.txt` file to enable document Q&A.
- Type `/search your question` to run a live Tavily web search when you need up-to-date info.
- Type `/chart 200` (or any number between 20 and 2000) to visualize a Seaborn histogram right in the chat.

### Assistants

This application supports multiple specialized assistants:

- **List assistants**: Type `/assistant list` to see all available assistants
- **Switch assistant**: Type `/assistant <name>` to switch your default assistant
- **Use assistant directly**: Type `/<command> <message>` to use a specific assistant (e.g., `/health schedule appointment`)

**Shared commands** (work with any assistant):
- `/search <query>`: Web search
- `/chart <size>`: Generate visualization
- File uploads: Process documents for Q&A