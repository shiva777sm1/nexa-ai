// React se zaroori "hooks" import kar rahe hain
// useState: data store karne ke liye (jaise email, messages list, etc.)
// useRef: kisi DOM element ko directly REFERENCE karne ke liye (jaise WebSocket object ko yaad rakhna)
// useEffect: component load/update hone pe kuch extra kaam karne ke liye
import { useState, useRef, useEffect } from "react";

// TypeScript "type" define kar rahe hain - ye batata hai ek Message object
// mein KYA-KYA fields honi chahiye. Isse galtiyan pakadna aasan ho jata hai
// (jaise agar hum "role" likhna bhool jayein, TypeScript turant error dega).
type Message = {
  role: "user" | "assistant"; // sirf ye 2 values allowed hain, kuch aur nahi
  content: string;
};

// Ye main component hai - poora chat app isी ke andar hai
function App() {
  // ===== STATE VARIABLES (data jo change hota rehta hai) =====

  // Login form ke fields
  const [email, setEmail] = useState("test@example.com");
  const [password, setPassword] = useState("test123");

  // Kya user login hai ya nahi (ye decide karega login form dikhe ya chat)
  const [authToken, setAuthToken] = useState<string | null>(null);

  // Login/register mein koi error/success message
  const [authMessage, setAuthMessage] = useState("");

  // WebSocket connected hai ya nahi
  const [isConnected, setIsConnected] = useState(false);

  // Saare chat messages ki list
  const [messages, setMessages] = useState<Message[]>([]);

  // Chat input box ka current text
  const [currentInput, setCurrentInput] = useState("");

  // Kya AI abhi reply "type" kar raha hai (streaming chal rahi hai)
  // Jab tak ye true hai, user naya message NAHI bhej payega
  const [isStreaming, setIsStreaming] = useState(false);

  // ===== REFS (values jo re-render trigger nahi karti, bas yaad rakhne ke liye) =====

  // WebSocket connection object ko yaad rakhne ke liye
  // (useState ki jagah useRef isliye, kyunki WebSocket object change hone pe
  // humein UI re-render nahi karwana - bas reference chahiye)
  const wsRef = useRef<WebSocket | null>(null);

  // Chat ke sabse neeche wala empty div - isse hum auto-scroll karenge
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  // Streaming ke dauraan AI ka reply जो अभी बन रहा है, usko track karne ke liye
  const streamingContentRef = useRef<string>("");

  // ===== FUNCTIONS =====

  // Register karne ka function
  const register = async () => {
    const res = await fetch("http://127.0.0.1:8000/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();

    if (data.error) {
      setAuthMessage(data.error);
    } else {
      setAuthMessage("Account created. Sign in to continue.");
    }
  };

  // Login karne ka function
  const login = async () => {
    const res = await fetch("http://127.0.0.1:8000/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();

    if (data.error) {
      setAuthMessage(data.error);
      return;
    }

    // Token save karo state mein - isse UI automatically chat screen pe switch ho jayega
    setAuthToken(data.access_token);
  };

  // Logout karne ka function
  const logout = () => {
    if (wsRef.current) wsRef.current.close();
    setAuthToken(null);
    setMessages([]);
    setIsConnected(false);
  };

  // Message bhejne ka function
  const sendMessage = () => {
    const trimmed = currentInput.trim();
    // Agar message khali hai, WebSocket connected nahi hai, YA AI abhi reply likh raha hai,
    // to kuch mat karo (user ko wait karna hoga)
    if (!trimmed || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN || isStreaming) {
      return;
    }

    // User ka message turant UI mein add karo (list mein purane messages + naya message)
    setMessages((prev) => [...prev, { role: "user", content: trimmed }]);

    // Backend ko message bhejo
    wsRef.current.send(trimmed);

    // Input box khali karo
    setCurrentInput("");

    // AI ka reply aana shuru hoga - ab user ko wait karana hai
    setIsStreaming(true);
  };

  // ===== USEEFFECT: Jab authToken change ho (login/logout ho), WebSocket connect/disconnect karo =====
  useEffect(() => {
    // Agar token nahi hai (logout ho gaya), kuch mat karo
    if (!authToken) return;

    // WebSocket connect karne ka function (reconnect ke liye bhi reuse hoga)
    const connect = () => {
      const ws = new WebSocket(`ws://127.0.0.1:8000/ws/chat?token=${authToken}`);

      ws.onopen = () => setIsConnected(true);

      ws.onclose = () => {
        setIsConnected(false);
        // Agar abhi bhi logged in hain (galti se disconnect hua), 2 second baad retry karo
        if (authToken) setTimeout(connect, 2000);
      };

      ws.onmessage = (event) => {
        if (event.data === "[END]") {
          // AI ka poora reply aa chuka - streaming buffer khali karo
          streamingContentRef.current = "";
          // Ab user dobara message bhej sakta hai
          setIsStreaming(false);
          return;
        }

        // Naya chunk aaya - use streaming buffer mein jodo
        streamingContentRef.current += event.data;

        // Messages list update karo: agar last message AI ka hai (abhi ban raha hai),
        // usko update karo. Warna ek NAYA AI message add karo.
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last && last.role === "assistant" && streamingContentRef.current.length > event.data.length) {
            // Purana AI message hai, usme naya chunk jodo (poora updated content use karo)
            const updated = [...prev];
            updated[updated.length - 1] = { role: "assistant", content: streamingContentRef.current };
            return updated;
          } else {
            // Naya AI message shuru ho raha hai
            return [...prev, { role: "assistant", content: streamingContentRef.current }];
          }
        });
      };

      wsRef.current = ws;
    };

    connect();

    // Cleanup: jab component hate ya authToken change ho, purana connection band karo
    return () => {
      wsRef.current?.close();
    };
  }, [authToken]); // Ye effect sirf tab chalega jab authToken change ho

  // ===== USEEFFECT: Jab naya message aaye, auto-scroll neeche karo =====
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ===== RENDER (JSX - jo screen pe dikhega) =====

  // Agar login nahi hai, LOGIN FORM dikhao
  if (!authToken) {
    return (
      <div className="shell">
        <div className="mark">
          <div className="mark-dot"></div>
          <div className="mark-text">Nexa AI</div>
        </div>

        <div className="card">
          <h1>Sign in</h1>
          <p className="sub">Connect to your assistant and pick up where you left off.</p>

          <div className="field">
            <label>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className="field">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <div className="btn-row">
            <button className="btn-primary" onClick={login}>Sign in</button>
            <button className="btn-ghost" onClick={register}>Create account</button>
          </div>
          {authMessage && <p className="auth-msg">{authMessage}</p>}
        </div>
      </div>
    );
  }

  // Agar login hai, CHAT INTERFACE dikhao
  return (
    <div className="shell">
      <div className="mark">
        <div className="mark-dot"></div>
        <div className="mark-text">Nexa AI</div>
      </div>

      <div className="chat-shell">
        <div className="chat-header">
          <div className={`status ${isConnected ? "live" : ""}`}>
            <div className="status-dot"></div>
            <span>{isConnected ? "Connected" : "Reconnecting..."}</span>
          </div>
          <button className="logout-link" onClick={logout}>Sign out</button>
        </div>

        <div id="chat">
          {/* .map() se har message ko ek bubble mein render kar rahe hain */}
          {messages.map((msg, index) => (
            <div key={index} className={`row ${msg.role === "user" ? "user" : "ai"}`}>
              <div className="bubble">{msg.content}</div>
            </div>
          ))}
          {/* Ye khali div sirf auto-scroll ke liye hai */}
          <div ref={chatEndRef}></div>
        </div>

        <div className="input-bar">
          <input
            type="text"
            placeholder={isStreaming ? "Nexa is typing..." : "Message Nexa..."}
            value={currentInput}
            disabled={isStreaming}
            onChange={(e) => setCurrentInput(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === "Enter") sendMessage();
            }}
          />
          <button className="send-btn" onClick={sendMessage} disabled={isStreaming}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;