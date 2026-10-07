export default function DataEntry() {
  return (
    <div>
      <div className="page-head">
        <div>
          <h1>Data Entry</h1>
          <div className="muted">
            Add battery sensor and aging data.
          </div>
        </div>
      </div>

      <div className="state">
        <h2>Battery data entry</h2>
        <p className="muted">
          Sensor readings, electrical data, coolant flow and aging records
          will be entered here.
        </p>
        <button className="btn" disabled>
          Add reading
        </button>
      </div>
    </div>
  );
}