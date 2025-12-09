import React from 'react';
import Sidebar from './Sidebar';
import { Outlet } from 'react-router-dom';

import HeroBackground from './HeroBackground';

const Layout = () => {
    return (
        <div className="flex min-h-screen text-white relative font-sans">
            <HeroBackground />
            <Sidebar />
            <main className="flex-1 ml-64 p-8 overflow-y-auto h-screen relative z-10">
                <Outlet />
            </main>
        </div>
    );
};

export default Layout;
