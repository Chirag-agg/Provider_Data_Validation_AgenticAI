import React, { useEffect, useRef } from 'react';
import gsap from 'gsap';

const HeroBackground = () => {
    const bgRef = useRef(null);
    const shape1Ref = useRef(null);
    const shape2Ref = useRef(null);

    useEffect(() => {
        // Parallax/Float Effect for shapes
        gsap.to(shape1Ref.current, {
            y: 40,
            rotation: 360,
            duration: 20,
            repeat: -1,
            yoyo: true,
            ease: "sine.inOut"
        });

        gsap.to(shape2Ref.current, {
            y: -50,
            rotation: -180,
            duration: 25,
            repeat: -1,
            yoyo: true,
            ease: "sine.inOut",
            delay: 1
        });

        // Background slow pulse
        gsap.to(bgRef.current, {
            scale: 1.05,
            duration: 15,
            repeat: -1,
            yoyo: true,
            ease: "sine.inOut"
        });
    }, []);

    return (
        <div className="fixed inset-0 z-[-1] overflow-hidden bg-background">
            {/* Main Gradient Background */}
            <div ref={bgRef} className="absolute inset-0 bg-[url('/hero-bg.png')] bg-cover bg-center opacity-60 mix-blend-screen" />

            {/* Overlay Gradient for depth */}
            <div className="absolute inset-0 bg-gradient-to-b from-background/20 via-background/60 to-background/90" />

            {/* Animated Floating Shapes */}
            <img
                ref={shape1Ref}
                src="/shape1.png"
                alt=""
                className="absolute top-10 right-10 w-96 h-96 object-contain opacity-60 blur-sm mix-blend-screen animate-float"
            />
            <img
                ref={shape2Ref}
                src="/shape2.png"
                alt=""
                className="absolute bottom-20 left-10 w-80 h-80 object-contain opacity-40 blur-xl mix-blend-screen"
            />

            {/* Noise Texture for "Grain" effect */}
            <div className="absolute inset-0 opacity-[0.03] pointer-events-none" style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")` }}></div>
        </div>
    );
};

export default HeroBackground;
