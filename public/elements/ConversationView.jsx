export default function ConversationView(props) {
  // Chainlit passes props as an object
  // Handle both direct props and nested props structure
  const conversation = props?.conversation || props?.props?.conversation || [];
  
  // Debug logging
  if (typeof window !== 'undefined' && window.console) {
    console.log('ConversationView rendered with props:', JSON.stringify(props, null, 2));
    console.log('ConversationView conversation:', conversation);
    console.log('ConversationView conversation length:', conversation?.length);
  }
  
  if (!conversation || conversation.length === 0) {
    return <div>No conversation data available</div>;
  }
  
  return (
    <>
      <style>{`
        .conversation-view {
          margin-top: 12px;
          margin-bottom: 12px;
        }
        
        .conversation-item {
          display: flex;
          margin-bottom: 12px;
          border-radius: 6px;
          overflow: hidden;
          padding: 12px 16px;
          transition: background-color 0.2s ease;
        }
        
        /* ATC - Blue colors (more vibrant) */
        .conversation-item.atc {
          border-left: 4px solid #2563eb;
          background-color: rgba(59, 130, 246, 0.15);
        }
        
        .conversation-item.atc .role-name {
          color: #1e40af;
          font-weight: 700;
        }
        
        .conversation-item.atc .message-text {
          color: #1e3a8a;
        }
        
        /* Pilot - Rose/Pink colors (more vibrant) */
        .conversation-item.pilot {
          border-left: 4px solid #e11d48;
          background-color: rgba(236, 72, 153, 0.15);
        }
        
        .conversation-item.pilot .role-name {
          color: #9f1239;
          font-weight: 700;
        }
        
        .conversation-item.pilot .message-text {
          color: #881337;
        }
        
        /* Dark theme overrides */
        @media (prefers-color-scheme: dark) {
          .conversation-item.atc {
            border-left-color: #60a5fa;
            background-color: rgba(30, 58, 138, 0.4);
          }
          
          .conversation-item.atc .role-name {
            color: #93c5fd;
            font-weight: 700;
          }
          
          .conversation-item.atc .message-text {
            color: #bfdbfe;
          }
          
          .conversation-item.pilot {
            border-left-color: #f472b6;
            background-color: rgba(131, 24, 67, 0.4);
          }
          
          .conversation-item.pilot .role-name {
            color: #fbcfe8;
            font-weight: 700;
          }
          
          .conversation-item.pilot .message-text {
            color: #fce7f3;
          }
        }
        
        /* Use Chainlit's theme variables if available */
        [data-theme="dark"] .conversation-item.atc {
          border-left-color: #60a5fa;
          background-color: rgba(30, 58, 138, 0.4);
        }
        
        [data-theme="dark"] .conversation-item.atc .role-name {
          color: #93c5fd;
          font-weight: 700;
        }
        
        [data-theme="dark"] .conversation-item.atc .message-text {
          color: #bfdbfe;
        }
        
        [data-theme="dark"] .conversation-item.pilot {
          border-left-color: #f472b6;
          background-color: rgba(131, 24, 67, 0.4);
        }
        
        [data-theme="dark"] .conversation-item.pilot .role-name {
          color: #fbcfe8;
          font-weight: 700;
        }
        
        [data-theme="dark"] .conversation-item.pilot .message-text {
          color: #fce7f3;
        }
        
        .role-name {
          font-weight: bold;
          font-size: 0.95em;
          margin-bottom: 6px;
        }
        
        .message-text {
          font-size: 0.9em;
          line-height: 1.5;
        }
      `}</style>
      <div className="conversation-view">
        {conversation.map((item, index) => {
          const role = item?.role || 'unknown';
          const message = item?.message || '';
          const roleClass = role.toLowerCase() === 'atc' ? 'atc' : 'pilot';
          
          return (
            <div
              key={index}
              className={`conversation-item ${roleClass}`}
            >
              <div style={{ flex: 1 }}>
                <div className="role-name">
                  {role.toUpperCase()}
                </div>
                <div className="message-text">
                  {message}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </>
  );
}

