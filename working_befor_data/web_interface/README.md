# Web Interface Directory

## Interface Components

### HTML Pages
- `index.html`: Main dashboard
  * Overview of routing system
  * Current status
  * Quick actions

- `sla.html`: SLA management
  * SLA monitoring
  * Performance metrics
  * SLA updates

- `event_index.html`: Event monitoring
  * Real-time events
  * Event history
  * Event actions

### Servers
- `server.py`: Main web server
  * Serves dashboard
  * Handles API requests
  * WebSocket support

- `sla_server.py`: SLA update server
  * Handles SLA updates
  * Real-time monitoring
  * SLA notifications

- `event_server.py`: Event handling server
  * Real-time event processing
  * Event broadcasting
  * Event persistence

## Required Files
```
web_interface/
├── README.md           # This documentation
├── index.html         # Main dashboard
├── sla.html          # SLA management
├── event_index.html  # Event monitoring
├── server.py         # Main server
├── sla_server.py     # SLA server
└── event_server.py   # Event server
```

## Features

### Dashboard
- System overview
- Current routing status
- Performance metrics
- Quick actions
- Real-time updates

### SLA Management
- SLA monitoring
- Performance tracking
- Update interface
- Historical data
- Alerts and notifications

### Event System
- Real-time event monitoring
- Event history
- Action triggers
- Event filtering
- Notification system

## Running the Interface

1. Start the main server:
```bash
python server.py
```

2. Start the SLA server:
```bash
python sla_server.py
```

3. Start the event server:
```bash
python event_server.py
```

4. Access the interfaces:
- Main Dashboard: http://localhost:8000
- SLA Management: http://localhost:8001
- Event Monitor: http://localhost:8002

## WebSocket Events

### SLA Updates
```javascript
// Subscribe to SLA updates
socket.on('sla_update', (data) => {
    updateSLADisplay(data);
});

// Send SLA update
socket.emit('update_sla', {
    link_id: 'LINK_001',
    new_sla: 95.0
});
```

### Event Monitoring
```javascript
// Subscribe to events
socket.on('new_event', (event) => {
    displayEvent(event);
});

// Send event
socket.emit('trigger_event', {
    type: 'price_change',
    link_id: 'LINK_001',
    new_price: 10.5
});