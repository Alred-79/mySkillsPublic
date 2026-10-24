import { useEffect, useState } from 'react';
import './palette.css';

const COMMANDS = ['New invoice', 'Find customer', 'Export ledger', 'Switch workspace', 'Open settings', 'Copy invoice link'];

export default function CommandPalette({ open, onClose, onRun }) {
  const [query, setQuery] = useState('');
  const [active, setActive] = useState(0);
  const [toast, setToast] = useState(null);
  const items = COMMANDS.filter((c) => c.toLowerCase().includes(query.toLowerCase()));

  useEffect(() => {
    if (!open) return;
    const onKey = (e) => {
      if (e.key === 'ArrowDown') setActive((i) => Math.min(i + 1, items.length - 1));
      if (e.key === 'ArrowUp') setActive((i) => Math.max(i - 1, 0));
      if (e.key === 'Escape') onClose();
      if (e.key === 'Enter' && items[active]) run(items[active]);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  });

  const run = (cmd) => {
    onRun(cmd);
    if (cmd === 'Copy invoice link') {
      setToast('Link copied');
      setTimeout(() => setToast(null), 2000);
    }
    onClose();
  };

  return (
    <>
      {open && (
        <div className="backdrop" onClick={onClose}>
          <div className="palette" role="dialog" aria-label="Command palette" onClick={(e) => e.stopPropagation()}>
            <input autoFocus value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Type a command" />
            <ul role="listbox">
              {items.map((c, i) => (
                <li key={c} role="option" aria-selected={i === active} className={i === active ? 'item active' : 'item'} onClick={() => run(c)}>
                  {c}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
      {toast && <div className="toast" role="status">{toast}</div>}
    </>
  );
}
