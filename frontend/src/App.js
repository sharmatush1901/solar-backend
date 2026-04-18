import { useState, useEffect } from "react";

function App() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [sessionId, setSessionId] = useState(Date.now().toString());
  const [loading, setLoading] = useState(false);
  const [darkMode, setDarkMode] = useState(false);

  const API = "http://127.0.0.1:8000";

  // ===============================
  // LOAD CHAT HISTORY
  // ===============================
  const loadHistory = async (id) => {
    try {
      const res = await fetch(`${API}/chat/history/${id}`);
      const data = await res.json();
      setMessages(data);
      setSessionId(id);
    } catch {
      console.log("Failed to load history");
    }
  };

  // ===============================
  // SEND MESSAGE (STREAMING)
  // ===============================
  const sendMessage = async () => {
    if (!query.trim()) return;

    const userMessage = { role: "user", text: query };
    setMessages((prev) => [...prev, userMessage]);

    setQuery("");
    setLoading(true);

    // add session to sidebar
    setSessions((prev) => {
      if (!prev.includes(sessionId)) {
        return [sessionId, ...prev];
      }
      return prev;
    });

    try {
      const res = await fetch(`${API}/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query,
          session_id: sessionId,
        }),
      });

      const reader = res.body.getReader();
      let text = "";

      setMessages((prev) => [...prev, { role: "bot", text: "" }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        text += new TextDecoder().decode(value);

        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1].text = text;
          return updated;
        });
      }

    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "bot", text: "❌ Server error" },
      ]);
    }

    setLoading(false);
  };

  // ===============================
  // FILE UPLOAD
  // ===============================
  const uploadFile = async (file) => {
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API}/upload/pdf`, {
        method: "POST",
        body: formData,
      });

      alert(res.ok ? "✅ PDF Uploaded" : "❌ Upload failed");
    } catch {
      alert("❌ Server not reachable");
    }
  };

  // ===============================
  // NEW CHAT
  // ===============================
  const newChat = () => {
    const id = Date.now().toString();
    setSessionId(id);
    setMessages([]);
  };

  const handleKey = (e) => {
    if (e.key === "Enter") sendMessage();
  };

  // ===============================
  // STYLES
  // ===============================
  const theme = {
    bg: darkMode ? "#0f172a" : "#f5f5f5",
    text: darkMode ? "#fff" : "#000",
    sidebar: darkMode ? "#020617" : "#111",
    bot: darkMode ? "#1e293b" : "#e5e5ea",
  };

  // ===============================
  // UI
  // ===============================
  return (
    <div style={{ display: "flex", height: "100vh", background: theme.bg, color: theme.text }}>

      {/* SIDEBAR */}
      <div style={{
        width: "260px",
        background: theme.sidebar,
        color: "white",
        padding: "15px",
        display: "flex",
        flexDirection: "column"
      }}>
        <h3>💬 Chats</h3>

        <button onClick={newChat} style={{ marginBottom: 10 }}>
          ➕ New Chat
        </button>

        {sessions.map((id) => (
          <div
            key={id}
            onClick={() => loadHistory(id)}
            style={{
              padding: "8px",
              background: "#222",
              marginBottom: "5px",
              borderRadius: "6px",
              cursor: "pointer"
            }}
          >
            Chat {id.slice(-4)}
          </div>
        ))}

        <button onClick={() => setDarkMode(!darkMode)} style={{ marginTop: "auto" }}>
          {darkMode ? "☀️ Light" : "🌙 Dark"}
        </button>
      </div>

      {/* MAIN */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>

        {/* HEADER */}
        <div style={{
          padding: 15,
          borderBottom: "1px solid #ccc",
          fontWeight: "bold",
          fontSize: "20px"
        }}>
          🌞 The Sun Son's Solar Solutions
        </div>

        {/* UPLOAD */}
        <div style={{ padding: 10 }}>
          <input type="file" onChange={(e) => uploadFile(e.target.files[0])} />
        </div>

        {/* CHAT AREA */}
        <div style={{
          flex: 1,
          overflowY: "auto",
          padding: 20,
          display: "flex",
          flexDirection: "column",
          gap: 10
        }}>
          {messages.map((msg, i) => (
            <div key={i} style={{
              display: "flex",
              justifyContent: msg.role === "user" ? "flex-end" : "flex-start"
            }}>
              <div style={{
                padding: "10px 14px",
                borderRadius: "12px",
                maxWidth: "60%",
                background: msg.role === "user" ? "#2563eb" : theme.bot,
                color: msg.role === "user" ? "white" : theme.text
              }}>
                {msg.text}
              </div>
            </div>
          ))}

          {loading && (
            <div style={{ fontStyle: "italic", opacity: 0.7 }}>
              🤖 Thinking...
            </div>
          )}
        </div>

        {/* INPUT */}
        <div style={{ display: "flex", padding: 10, gap: 10 }}>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Ask something..."
            style={{ flex: 1, padding: 10, borderRadius: 8 }}
          />
          <button onClick={sendMessage}>Send</button>
        </div>
      </div>
    </div>
  );
}

export default App;1