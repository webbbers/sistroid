import axios from 'axios';

const instance = axios.create({
    baseURL: 'http://localhost:1999'
});

export default instance;