import { useEffect, useState } from 'react';
import { Shield, Users as UsersIcon, Settings, BarChart } from 'lucide-react';
import { useLocation } from 'react-router-dom';

export default function AdminPages() {
  const location = useLocation();
  const path = location.pathname.split('/').pop();

  const [users, setUsers] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);

  useEffect(() => {
    if (path === 'users') {
      fetch('http://localhost:8000/api/admin/users', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      }).then(r => r.json()).then(setUsers);
    } else if (path === 'audit') {
      fetch('http://localhost:8000/api/admin/audit_logs', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      }).then(r => r.json()).then(setAuditLogs);
    }
  }, [path]);

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-white capitalize">Admin: {path === 'audit' ? 'Audit Logs' : path}</h2>
      </div>

      <div className="glass-card overflow-hidden border border-slate-700/50 p-6">
        {path === 'users' && (
          <div>
            <div className="flex justify-between items-center mb-6">
               <h3 className="text-lg font-medium text-white">System Users</h3>
               <button className="btn-primary py-2 px-4 text-sm">Add User</button>
            </div>
            <table className="w-full text-sm">
              <thead className="bg-slate-900/40 text-slate-400">
                <tr>
                  <th className="px-4 py-3 text-left">Username</th>
                  <th className="px-4 py-3 text-left">Role</th>
                  <th className="px-4 py-3 text-left">Email</th>
                  <th className="px-4 py-3 text-left">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {users.map(u => (
                  <tr key={u.id} className="text-slate-300">
                    <td className="px-4 py-3 font-medium text-white">{u.username}</td>
                    <td className="px-4 py-3">
                       <span className="px-2 py-1 bg-blue-500/10 text-blue-400 rounded text-xs">{u.role}</span>
                    </td>
                    <td className="px-4 py-3 text-slate-400">{u.email}</td>
                    <td className="px-4 py-3 text-emerald-400">Active</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {path === 'audit' && (
          <div>
            <h3 className="text-lg font-medium text-white mb-6">System Audit Logs</h3>
            <table className="w-full text-sm">
              <thead className="bg-slate-900/40 text-slate-400">
                <tr>
                  <th className="px-4 py-3 text-left">Timestamp</th>
                  <th className="px-4 py-3 text-left">User</th>
                  <th className="px-4 py-3 text-left">Action</th>
                  <th className="px-4 py-3 text-left">Detail</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {auditLogs.map(log => (
                  <tr key={log.id} className="text-slate-300">
                    <td className="px-4 py-3 text-slate-400">{new Date(log.timestamp).toLocaleString()}</td>
                    <td className="px-4 py-3 font-medium text-blue-400">{log.username}</td>
                    <td className="px-4 py-3">{log.action}</td>
                    <td className="px-4 py-3 text-slate-400">{log.detail}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {(path === 'rules' || path === 'analytics') && (
           <div className="py-20 text-center text-slate-400 flex flex-col items-center">
             <Settings className="w-12 h-12 mb-4 opacity-50" />
             <h3 className="text-xl font-semibold text-white mb-2 capitalize">{path} Module</h3>
             <p>This module is currently in development for the next prototype phase.</p>
           </div>
        )}
      </div>
    </div>
  );
}
