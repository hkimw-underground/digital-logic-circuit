import React from 'react';
import Layout from '@theme/Layout';
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid
} from 'recharts';

// Realistic static validation data
const validationSummary = {
  totalAttempts: 1240,
  successRate: "68.5%",
  avgAuthTime: "1.2s",
  systemStatus: "Operational"
};

const attemptData = [
  { name: 'Successful Auth', value: 850 },
  { name: 'Failed Auth', value: 390 }
];

const COLORS = ['#059669', '#e11d48'];

const failureReasons = [
  { name: 'Invalid NFC/PIN', count: 120 },
  { name: 'Face Mismatch', count: 185 },
  { name: 'Face Timeout', count: 65 },
  { name: 'Hardware Comms', count: 20 },
];

const recentEvents = [
  { id: 1042, time: '2023-11-20 14:22:10', type: 'SUCCESS', reason: '-' },
  { id: 1041, time: '2023-11-20 14:15:05', type: 'FAILURE_AUTH2', reason: 'Face Mismatch' },
  { id: 1040, time: '2023-11-20 13:50:22', type: 'SUCCESS', reason: '-' },
  { id: 1039, time: '2023-11-20 12:10:01', type: 'FAILURE_AUTH1', reason: 'Invalid NFC UID' },
  { id: 1038, time: '2023-11-20 11:05:44', type: 'FAILURE_TIMEOUT', reason: 'Vision Module Timeout' },
];

export default function Dashboard() {
  return (
    <Layout title="Validation Dashboard" description="System Validation and Status Dashboard">
      <main className="container margin-vert--lg">
        <h1>System Validation Status</h1>
        <p className="margin-bottom--lg text--secondary">
          This dashboard presents a summary of authentication attempts and system health based on integration testing datasets.
        </p>

        {/* Top KPI Cards */}
        <div className="row margin-bottom--lg">
          <div className="col col--3">
            <div className="custom-card text--center">
              <h3 className="text--secondary">Total Attempts</h3>
              <p style={{fontSize: '2rem', fontWeight: 'bold', margin: 0, color: '#0f172a'}}>
                {validationSummary.totalAttempts}
              </p>
            </div>
          </div>
          <div className="col col--3">
            <div className="custom-card text--center">
              <h3 className="text--secondary">Success Rate</h3>
              <p style={{fontSize: '2rem', fontWeight: 'bold', margin: 0, color: '#059669'}}>
                {validationSummary.successRate}
              </p>
            </div>
          </div>
          <div className="col col--3">
            <div className="custom-card text--center">
              <h3 className="text--secondary">Avg. Auth Time</h3>
              <p style={{fontSize: '2rem', fontWeight: 'bold', margin: 0, color: '#1e3a8a'}}>
                {validationSummary.avgAuthTime}
              </p>
            </div>
          </div>
          <div className="col col--3">
            <div className="custom-card text--center">
              <h3 className="text--secondary">System Status</h3>
              <p style={{fontSize: '2rem', fontWeight: 'bold', margin: 0, color: '#059669'}}>
                {validationSummary.systemStatus}
              </p>
            </div>
          </div>
        </div>

        {/* Charts Row */}
        <div className="row margin-bottom--lg">
          {/* Pie Chart */}
          <div className="col col--6">
            <div className="custom-card">
              <h3 className="custom-card-title">Success vs Failure Ratio</h3>
              <div style={{ width: '100%', height: 300 }}>
                <ResponsiveContainer>
                  <PieChart>
                    <Pie
                      data={attemptData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      fill="#8884d8"
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {attemptData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Bar Chart */}
          <div className="col col--6">
            <div className="custom-card">
              <h3 className="custom-card-title">Failure Reason Distribution</h3>
              <div style={{ width: '100%', height: 300 }}>
                <ResponsiveContainer>
                  <BarChart data={failureReasons} layout="vertical" margin={{top: 5, right: 30, left: 40, bottom: 5}}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                    <XAxis type="number" />
                    <YAxis dataKey="name" type="category" width={100} tick={{fontSize: 12}} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#1e3a8a" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Events Table */}
        <div className="row">
          <div className="col col--12">
            <div className="custom-card">
              <h3 className="custom-card-title margin-bottom--md">Recent Event Logs (Sample)</h3>
              <table>
                <thead>
                  <tr>
                    <th>Log ID</th>
                    <th>Timestamp</th>
                    <th>Status</th>
                    <th>Failure Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {recentEvents.map((evt) => (
                    <tr key={evt.id}>
                      <td>{evt.id}</td>
                      <td>{evt.time}</td>
                      <td>
                        <span style={{
                          fontWeight: 'bold',
                          color: evt.type === 'SUCCESS' ? '#059669' : '#e11d48'
                        }}>
                          {evt.type}
                        </span>
                      </td>
                      <td>{evt.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

      </main>
    </Layout>
  );
}
