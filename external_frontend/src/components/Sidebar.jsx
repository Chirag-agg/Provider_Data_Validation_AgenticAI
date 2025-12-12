import React, { useRef, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  FileCheck,
  PlayCircle,
  ClipboardList,
  Settings,
  Activity
} from 'lucide-react';
import gsap from 'gsap';

const Sidebar = () => {
  const sidebarRef = useRef(null);
  const linksRef = useRef([]);

  useEffect(() => {
    gsap.fromTo(sidebarRef.current,
      { x: -100, opacity: 0 },
      { x: 0, opacity: 1, duration: 0.8, ease: 'power3.out' }
    );

    gsap.fromTo(linksRef.current,
      { x: -20, opacity: 0 },
      { x: 0, opacity: 1, duration: 0.5, stagger: 0.1, delay: 0.3, ease: 'power2.out' }
    );
  }, []);

  const navItems = [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/' },
    { icon: PlayCircle, label: 'Run Validation', path: '/validation' },
    { icon: Users, label: 'Directory', path: '/directory' },
    { icon: Activity, label: 'Drift Monitoring', path: '/drift-monitoring' },
    { icon: FileCheck, label: 'Manual Review', path: '/review' },
    { icon: ClipboardList, label: 'Activity Logs', path: '/logs' },
    { icon: Settings, label: 'Settings', path: '/settings' },
  ];

  return (
    <div ref={sidebarRef} className="h-screen w-64 bg-surface/30 backdrop-blur-xl border-r border-white/10 flex flex-col fixed left-0 top-0 z-50 shadow-glass">
      <div className="p-8">
        <h1 className="text-2xl font-poster text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent">
          Valid8
        </h1>
        <p className="text-xs text-slate-400 mt-1 uppercase tracking-widest">Provider Data</p>
      </div>

      <nav className="flex-1 px-4 flex flex-col justify-center gap-8">
        {navItems.map((item, index) => (
          <NavLink
            key={item.path}
            to={item.path}
            ref={el => linksRef.current[index] = el}
            className={({ isActive }) => `
              flex items-center gap-4 px-6 py-4 rounded-2xl transition-all duration-300 group
              ${isActive
                ? 'bg-primary/10 text-primary shadow-[0_0_20px_rgba(56,189,248,0.3)] border border-primary/20 scale-105'
                : 'text-slate-400 hover:bg-white/5 hover:text-white hover:translate-x-1'}
            `}
          >
            <item.icon size={24} className="group-hover:scale-110 transition-transform duration-300" />
            <span className="font-display font-bold tracking-wide text-lg">{item.label}</span>
          </NavLink>
        ))}
      </nav>


    </div >
  );
};

export default Sidebar;
