import {fit} from './lle-fit.js';
self.onmessage=({data})=>{try{self.postMessage({result:fit(data.rows,data.options)});}catch(error){self.postMessage({error:error.message});}};
