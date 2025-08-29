import React, { useState } from "react";
import { Swiper, SwiperSlide } from "swiper/react";
import { Pagination, Autoplay, Navigation } from "swiper/modules";

import "swiper/css";
import "swiper/css/pagination";
import "swiper/css/navigation";

import sample1 from "../../assets/10.jpg";
import sample2 from "../../assets/50.jpg";
import sample3 from "../../assets/150.jpg";

import sample4 from "../../assets/angel.jpg";
import sample5 from "../../assets/angel1.jpg";
import sample6 from "../../assets/angel3.jpg";



export default function HomePage() {
  const [showChoice, setShowChoice] = useState(false);

  const slides = [
    [sample1, sample2, sample3],
    [sample4, sample5, sample6],
  ];

  const handleTryNowClick = () => setShowChoice(true);

  const handleChoice = (path) => {
    setShowChoice(false);
    window.location.href = path;
  };

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-gray-50 relative">

      <div className="md:w-2/3 flex items-center justify-center bg-gray-900 p-4">
        <Swiper
          modules={[Pagination, Autoplay, Navigation]}
          navigation
          autoplay={{ delay: 3000, disableOnInteraction: false }}
          loop={true}
          spaceBetween={30}
          slidesPerView={1}
          className="w-full relative"
        >
          {slides.map((group, idx) => (
            <SwiperSlide key={idx}>
              <div className="relative flex justify-center gap-6 overflow-hidden p-6">
                {group.map((src, i) => (
                  <div
                    key={i}
                    className="w-40 h-60 md:w-60 md:h-[28rem] overflow-hidden rounded-lg"
                  >
                    <img
                      src={src}
                      alt={`Slide ${i}`}
                      className="w-full h-full object-cover rounded-lg animate-kenburns"
                    />
                  </div>
                ))}
                <div className="absolute inset-0 flex items-end justify-center pointer-events-none mb-2">
                  <h2 className="text-white text-3xl md:text-6xl font-extrabold text-center leading-tight drop-shadow-2xl tracking-tight">
                    Every <span className="text-red-500">Pixel</span> Matters
                  </h2>
                </div>

              </div>
            </SwiperSlide>
          ))}
        </Swiper>
      </div>

      {/* Right side */}
      <div className="md:w-1/3 flex flex-col justify-center p-6 md:p-12 space-y-32">
        <h1 className="text-2xl md:text-4xl font-bold text-gray-900">
          Breathing Life into Pixels
        </h1>
 <p className="text-gray-700 text-base md:text-lg leading-relaxed md:leading-loose">
  Forward Image Diffusion allows you to easily enhance and slightly
  diffuse your images, creating a smooth, artistic look. Perfect for
  designers, photographers, and creators.
</p>

        <button
          className="bg-gray-900 hover:bg-gray-700 text-white font-semibold py-3 px-6 rounded-lg  text-base md:text-lg w-40"
          onClick={handleTryNowClick}
        >
          Try Now
        </button>
      </div>

{showChoice && (
  <div className="absolute inset-0 flex items-center justify-center bg-black/70 backdrop-blur-sm z-50">
    <div className="bg-gradient-to-b from-zinc-900 to-zinc-800 border border-zinc-700/50 p-8 rounded-2xl shadow-2xl text-center space-y-6 w-[90%] max-w-md">
      <h3 className="text-2xl font-bold text-white">
        How would you like to continue?
      </h3>
      <div className="flex flex-col md:flex-row gap-4 justify-center">
        <button
          onClick={() => handleChoice("/login")}
          className="flex-1 bg-black/70 backdrop-blur-sm hover:bg-blue-500/10 text-white px-6 py-3 rounded-lg font-semibold transition-colors shadow-lg"
        >
          Login
        </button>
        <button
          onClick={() => handleChoice("/signup")}
          className="flex-1 bg-black/70 backdrop-blur-sm text-white hover:bg-blue-500/10 px-6 py-3 rounded-lg font-semibold transition-colors"
        >
          Sign Up
        </button>
      </div>

      <button
        onClick={() => setShowChoice(false)}
        className="text-zinc-400 hover:text-white text-sm transition-colors"
      >
        Cancel
      </button>
    </div>
  </div>
)}


      {/* Ken Burns animation */}
      <style>{`
        @keyframes kenburns {
          0% { transform: scale(1) translate(0, 0); }
          50% { transform: scale(1.1) translate(-5px, -5px); }
          100% { transform: scale(1) translate(0, 0); }
        }
        .animate-kenburns {
          animation: kenburns 12s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
}
