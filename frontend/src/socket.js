import { io } from 'socket.io-client';

const socket = io('http://localhost:5000', {
  transports: ['polling'],
  upgrade: false,
  autoConnect: true,
  // Don't reconnect too aggressively
  reconnectionDelay: 1000,
  reconnectionDelayMax: 5000
});

export default socket;