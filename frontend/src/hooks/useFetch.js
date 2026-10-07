import { useCallback, useEffect, useState } from "react";

// Small data-loading hook: { data, loading, error, reload, setData }
export function useFetch(fn, deps = []) {
  const [state, setState] = useState({ data: null, loading: true, error: null });
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let live = true;
    setState((s) => ({ ...s, loading: true, error: null }));
    fn()
      .then((data) => live && setState({ data, loading: false, error: null }))
      .catch((error) => live && setState({ data: null, loading: false, error }));
    return () => { live = false; };
    // eslint-disable-next-line
  }, [...deps, tick]);

  const reload = useCallback(() => setTick((t) => t + 1), []);
  const setData = useCallback(
    (u) => setState((s) => ({ ...s, data: typeof u === "function" ? u(s.data) : u })),
    []
  );
  return { ...state, reload, setData };
}
