export default function CollapsibleSection(props) {
  // Chainlit passes props as an object
  // Handle both direct props and nested props structure
  const title = props?.title || props?.props?.title || 'Click to expand';
  const content = props?.content || props?.props?.content || '';
  
  // Debug: log props to console to help diagnose
  if (typeof window !== 'undefined' && window.console) {
    console.log('CollapsibleSection all props:', JSON.stringify(props, null, 2));
    console.log('CollapsibleSection title:', title);
    console.log('CollapsibleSection content:', content);
    console.log('CollapsibleSection content type:', typeof content);
    console.log('CollapsibleSection content length:', content?.length);
  }
  
  return (
    <details className="collapsible-section" style={{ marginTop: '8px' }}>
      <summary 
        className="collapsible-header"
        style={{ 
          cursor: 'pointer', 
          userSelect: 'none',
          fontWeight: '500',
          padding: '4px 0'
        }}
      >
        {title}
      </summary>
      <div className="collapsible-content" style={{ marginTop: '8px' }}>
        <pre style={{ 
          whiteSpace: 'pre-wrap', 
          wordWrap: 'break-word',
          margin: 0,
          padding: '12px',
          backgroundColor: '#f5f5f5',
          borderRadius: '4px',
          fontSize: '0.9em',
          overflow: 'auto',
          maxHeight: '400px'
        }}>
          {content || '(No content provided)'}
        </pre>
      </div>
    </details>
  );
}

