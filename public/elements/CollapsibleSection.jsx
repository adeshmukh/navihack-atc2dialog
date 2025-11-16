export default function CollapsibleSection({ title, content }) {
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
        {title || 'Click to expand'}
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
          {content}
        </pre>
      </div>
    </details>
  );
}

