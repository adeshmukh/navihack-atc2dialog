export default function ConversationView(props) {
  // Chainlit passes props as an object
  // Handle both direct props and nested props structure
  const conversation = props?.conversation || props?.props?.conversation || [];
  
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
        
        /* ATC - Blue colors */
        .conversation-item.atc {
          border-left: 4px solid #3b82f6;
          background-color: rgba(59, 130, 246, 0.1);
        }
        
        .conversation-item.atc .role-name {
          color: #1e40af;
        }
        
        /* Pilot - Pink colors */
        .conversation-item.pilot {
          border-left: 4px solid #ec4899;
          background-color: rgba(236, 72, 153, 0.1);
        }
        
        .conversation-item.pilot .role-name {
          color: #9f1239;
        }
        
        /* Dark theme overrides */
        @media (prefers-color-scheme: dark) {
          .conversation-item.atc {
            border-left-color: #60a5fa;
            background-color: rgba(30, 58, 138, 0.3);
          }
          
          .conversation-item.atc .role-name {
            color: #93c5fd;
          }
          
          .conversation-item.pilot {
            border-left-color: #f472b6;
            background-color: rgba(131, 24, 67, 0.3);
          }
          
          .conversation-item.pilot .role-name {
            color: #fbcfe8;
          }
        }
        
        /* Use Chainlit's theme variables if available */
        [data-theme="dark"] .conversation-item.atc {
          border-left-color: #60a5fa;
          background-color: rgba(30, 58, 138, 0.3);
        }
        
        [data-theme="dark"] .conversation-item.atc .role-name {
          color: #93c5fd;
        }
        
        [data-theme="dark"] .conversation-item.pilot {
          border-left-color: #f472b6;
          background-color: rgba(131, 24, 67, 0.3);
        }
        
        [data-theme="dark"] .conversation-item.pilot .role-name {
          color: #fbcfe8;
        }
        
        .role-name {
          font-weight: bold;
          font-size: 0.95em;
          margin-bottom: 6px;
        }
        
        .message-text {
          font-size: 0.9em;
          line-height: 1.5;
          color: inherit;
        }
        
        /* Ensure text is readable in both themes */
        @media (prefers-color-scheme: dark) {
          .conversation-item .message-text {
            color: rgba(255, 255, 255, 0.9);
          }
        }
        
        [data-theme="dark"] .conversation-item .message-text {
          color: rgba(255, 255, 255, 0.9);
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

