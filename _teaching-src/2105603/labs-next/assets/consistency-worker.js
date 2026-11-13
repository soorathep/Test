import { modelingTest } from '../../labs/assets/consistency.js';
self.onmessage = ({ data }) => {
  try { self.postMessage({ result: modelingTest(data.set, data.properties) }); }
  catch (error) { self.postMessage({ error: error.message }); }
};
