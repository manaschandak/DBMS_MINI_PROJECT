export default function Feedback() {
  return (
    <div>
      <div className="page-head">
        <div>
          <h1>Feedback</h1>
          <div className="muted">
            Review prediction and alert outcomes.
          </div>
        </div>
      </div>

      <div className="state">
        <h2>Prediction feedback</h2>
        <p className="muted">
          Feedback on alerts and predictions will be displayed here.
        </p>
        <button className="btn" disabled>
          Submit feedback
        </button>
      </div>
    </div>
  );
}