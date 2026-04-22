import { useEffect, useMemo, useState } from "react";
import { searchByImage } from "./api";

const DEFAULT_LIMIT = 24;

export default function App() {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [category, setCategory] = useState("");
  const [limit, setLimit] = useState(DEFAULT_LIMIT);
  const [results, setResults] = useState([]);
  const [duration, setDuration] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!file) {
      setPreviewUrl("");
      return;
    }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const handleFileChange = (event) => {
    const selected = event.target.files?.[0];
    setFile(selected || null);
    setResults([]);
    setError("");
  };

  const handleSearch = async () => {
    if (!file) {
      setError("Upload an image to search.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const data = await searchByImage(file, { category, limit });
      setResults(data.results || []);
      setDuration(data.took_ms ?? null);
    } catch (err) {
      setError(err.message || "Search failed.");
    } finally {
      setLoading(false);
    }
  };

  const heroCopy = useMemo(
    () =>
      "Search for products by visual similarity. Drop an inspiration image and discover items with matching textures, patterns, and shapes.",
    []
  );

  return (
    <div className="page">
      <header className="hero">
        <div>
          <p className="eyebrow">Image Search Studio</p>
          <h1>Find the product behind the vibe.</h1>
        </div>
        <p className="subtitle">{heroCopy}</p>
        <div className="controls">
          <label className="file-input">
            <input type="file" accept="image/*" onChange={handleFileChange} />
            <span>{file ? "Change image" : "Upload inspiration"}</span>
          </label>
          <div className="field">
            <label htmlFor="category">Category</label>
            <input
              id="category"
              value={category}
              onChange={(event) => setCategory(event.target.value)}
              placeholder="Optional filter"
            />
          </div>
          <div className="field">
            <label htmlFor="limit">Max results</label>
            <input
              id="limit"
              type="number"
              min="1"
              max="50"
              value={limit}
              onChange={(event) => setLimit(Number(event.target.value))}
            />
          </div>
          <button className="primary" type="button" onClick={handleSearch} disabled={loading}>
            {loading ? "Searching..." : "Search"}
          </button>
        </div>
        {error ? <p className="error">{error}</p> : null}
      </header>

      <section className="workspace">
        <div className="preview-card">
          <h2>Query preview</h2>
          {previewUrl ? (
            <img src={previewUrl} alt="Preview" />
          ) : (
            <div className="placeholder">Drop a product photo to preview.</div>
          )}
          {duration !== null ? (
            <p className="meta">Search time: {duration} ms</p>
          ) : null}
        </div>

        <div className="results">
          <div className="results-header">
            <h2>Similar finds</h2>
            <p>{results.length ? `${results.length} matches` : "No matches yet."}</p>
          </div>
          <div className="grid">
            {results.map((item) => (
              <article key={item.id} className="card">
                <div className="card-image">
                  <img
                    src={item.image_path}
                    alt={item.title}
                    onError={(event) => {
                      event.currentTarget.src = "https://placehold.co/400x400?text=Image";
                    }}
                  />
                </div>
                <div className="card-body">
                  <h3>{item.title}</h3>
                  <p className="card-meta">{item.category || "Uncategorized"}</p>
                  {item.score !== null ? (
                    <p className="score">Similarity: {(item.score * 100).toFixed(1)}%</p>
                  ) : null}
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
