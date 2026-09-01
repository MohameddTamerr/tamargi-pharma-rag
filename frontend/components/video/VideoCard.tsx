"use client";

import { useState } from "react";
import { VideoItem } from "@/lib/api";
import { Play, ShieldCheck, ExternalLink, X, Film, Volume2 } from "lucide-react";

interface VideoCardProps {
  video: VideoItem;
}

function getEmbedUrl(url: string): string | null {
  if (!url) return null;

  // YouTube standard or short links
  const ytMatch = url.match(/(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([\w-]{11})/);
  if (ytMatch && ytMatch[1]) {
    return `https://www.youtube-nocookie.com/embed/${ytMatch[1]}?autoplay=1&rel=0`;
  }

  // Vimeo links
  const vimeoMatch = url.match(/vimeo\.com\/(?:channels\/(?:\w+\/)?|groups\/([^\/]*)\/videos\/|album\/(\d+)\/video\/|)(\d+)(?:$|\/|\?)/);
  if (vimeoMatch && vimeoMatch[3]) {
    return `https://player.vimeo.com/video/${vimeoMatch[3]}?autoplay=1`;
  }

  // Direct MP4 / WebM video files
  if (url.endsWith(".mp4") || url.endsWith(".webm") || url.endsWith(".ogg")) {
    return url;
  }

  return null;
}

export default function VideoCard({ video }: VideoCardProps) {
  const [isPlaying, setIsPlaying] = useState(false);

  if (!video || !video.video_url) return null;

  const embedUrl = getEmbedUrl(video.video_url);
  const isDirectFile = video.video_url.endsWith(".mp4") || video.video_url.endsWith(".webm");

  return (
    <div className="mt-3 overflow-hidden rounded-2xl bg-slate-900 border border-slate-700/80 shadow-lg transition-all hover:border-blue-500/50">
      
      {/* Top Header Badge */}
      <div className="flex items-center justify-between px-3.5 py-2 bg-slate-950/80 border-b border-slate-800/80 text-[11px]">
        <div className="flex items-center gap-1.5 text-emerald-400 font-semibold">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>فيديو طبي تعليمي معتمد</span>
        </div>

        <div className="flex items-center gap-1.5 flex-wrap">
          {video.device_name && (
            <span className="px-2 py-0.5 rounded-md bg-blue-950 border border-blue-800 text-blue-300 font-bold text-[10px]">
              {video.device_name}
            </span>
          )}
          {video.device_type && (
            <span className="px-2 py-0.5 rounded-md bg-slate-800 text-cyan-300 font-mono text-[10px]">
              {video.device_type}
            </span>
          )}
          {video.language && (
            <span className="px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 font-medium text-[10px] uppercase">
              {video.language === "ar" ? "عربي" : video.language}
            </span>
          )}
          <span className="text-slate-400 text-[10px] hidden sm:inline">{video.source_name}</span>
        </div>
      </div>

      {/* Main Content Layout */}
      <div className="flex flex-col sm:flex-row items-center gap-3 p-3">
        
        {/* Video Thumbnail / Preview Area */}
        <div className="relative w-full sm:w-44 h-28 shrink-0 rounded-xl overflow-hidden bg-slate-950 border border-slate-800 flex items-center justify-center group">
          {video.thumbnail_url ? (
            <img
              src={video.thumbnail_url}
              alt={video.title}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            />
          ) : (
            <div className="w-full h-full bg-gradient-to-br from-slate-900 to-blue-950 flex flex-col items-center justify-center gap-1 text-slate-500">
              <Film className="w-8 h-8 text-blue-400/60" />
              <span className="text-[10px] text-slate-400 font-medium">Tamargi Video</span>
            </div>
          )}

          {/* Semi-transparent Overlay with Play Button */}
          <button
            type="button"
            onClick={() => {
              if (embedUrl) {
                setIsPlaying(true);
              } else {
                window.open(video.video_url, "_blank", "noopener,noreferrer");
              }
            }}
            className="absolute inset-0 bg-black/40 hover:bg-black/20 flex items-center justify-center transition-colors"
            title="تشغيل الفيديو التعليمي"
          >
            <div className="w-10 h-10 rounded-full bg-blue-600/90 hover:bg-blue-500 text-white flex items-center justify-center shadow-lg shadow-blue-600/40 transform group-hover:scale-110 transition-transform">
              <Play className="w-4 h-4 ml-0.5 fill-current" />
            </div>
          </button>
        </div>

        {/* Video Information & Actions */}
        <div className="flex-1 flex flex-col justify-between self-stretch space-y-2 text-right">
          <div>
            <h4 className="text-sm font-bold text-slate-100 line-clamp-2 leading-snug">
              {video.title}
            </h4>
            <p className="text-[11px] text-slate-400 mt-1 line-clamp-1">
              المصدر الموثوق: <span className="text-slate-300 font-medium">{video.source_name}</span>
            </p>
          </div>

          <div className="flex items-center gap-2 pt-1">
            <button
              type="button"
              onClick={() => {
                if (embedUrl) {
                  setIsPlaying(true);
                } else {
                  window.open(video.video_url, "_blank", "noopener,noreferrer");
                }
              }}
              className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs flex items-center gap-1.5 shadow-sm transition-colors"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>مشاهدة الشرح</span>
            </button>

            <a
              href={video.source_url || video.video_url}
              target="_blank"
              rel="noopener noreferrer"
              className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs flex items-center gap-1 transition-colors"
              title="فتح الرابط في صفحة خارجية"
            >
              <span>المصدر</span>
              <ExternalLink className="w-3 h-3 text-slate-400" />
            </a>
          </div>
        </div>

      </div>

      {/* Embedded Video Modal Player */}
      {isPlaying && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in">
          <div className="relative w-full max-w-3xl bg-slate-900 border border-slate-700 rounded-2xl overflow-hidden shadow-2xl">
            
            {/* Modal Header */}
            <div className="flex items-center justify-between px-4 py-3 bg-slate-950 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-bold text-slate-200 line-clamp-1">{video.title}</span>
              </div>
              
              <button
                type="button"
                onClick={() => setIsPlaying(false)}
                className="p-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                title="إغلاق الفيديو"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Video Player Frame */}
            <div className="relative w-full aspect-video bg-black">
              {isDirectFile ? (
                <video
                  src={video.video_url}
                  controls
                  autoPlay
                  className="w-full h-full"
                >
                  متصفحك لا يدعم تشغيل هذا الفيديو.
                </video>
              ) : embedUrl ? (
                <iframe
                  src={embedUrl}
                  title={video.title}
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                  className="w-full h-full border-none"
                />
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-center p-6 space-y-3">
                  <p className="text-sm text-slate-300">
                    هذا الفيديو لا يدعم التشغيل المباشر داخل الصفحة.
                  </p>
                  <a
                    href={video.video_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold flex items-center gap-2"
                  >
                    <span>فتح الفيديو في نافذة خارجية</span>
                    <ExternalLink className="w-4 h-4" />
                  </a>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-between px-4 py-2 bg-slate-950 text-[11px] text-slate-400">
              <span>المصدر المعتمد: {video.source_name}</span>
              <a
                href={video.video_url}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-blue-400 flex items-center gap-1 transition-colors"
              >
                <span>رابط خارجي</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>

          </div>
        </div>
      )}

    </div>
  );
}
