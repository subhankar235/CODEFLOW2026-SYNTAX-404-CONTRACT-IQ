"use client";

import { UserProfile } from "@clerk/nextjs";
import { dark } from "@clerk/themes";
import { Settings, Shield, Bell, Key } from "lucide-react";
import { useState } from "react";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("profile");

  return (
    <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 relative flex flex-col md:flex-row gap-6 lg:gap-10">
      {/* Sidebar Navigation for Settings */}
      <div className="w-full md:w-56 lg:w-64 shrink-0">
        <h1 className="text-2xl font-bold text-white mb-6">Settings</h1>
        <nav className="space-y-1">
          <button 
            onClick={() => setActiveTab("profile")}
            className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
              activeTab === "profile" 
                ? "bg-white/10 text-white border border-white/10" 
                : "text-zinc-400 hover:text-white hover:bg-white/5"
            }`}
          >
            <Settings className="h-4 w-4" /> Account Profile
          </button>
          <button 
            onClick={() => setActiveTab("security")}
            className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
              activeTab === "security" 
                ? "bg-white/10 text-white border border-white/10" 
                : "text-zinc-400 hover:text-white hover:bg-white/5"
            }`}
          >
            <Shield className="h-4 w-4" /> Security & Privacy
          </button>
          <button 
            onClick={() => setActiveTab("notifications")}
            className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
              activeTab === "notifications" 
                ? "bg-white/10 text-white border border-white/10" 
                : "text-zinc-400 hover:text-white hover:bg-white/5"
            }`}
          >
            <Bell className="h-4 w-4" /> Notifications
          </button>
          <button 
            onClick={() => setActiveTab("api")}
            className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
              activeTab === "api" 
                ? "bg-white/10 text-white border border-white/10" 
                : "text-zinc-400 hover:text-white hover:bg-white/5"
            }`}
          >
            <Key className="h-4 w-4" /> API Keys
          </button>
        </nav>
      </div>

      {/* Main Settings Content */}
      <div className="flex-1">
        {activeTab === "profile" && (
          <div className="glass-panel p-8 rounded-2xl border border-white/10 flex flex-col items-center">
            <div className="w-full max-w-xl">
              <h2 className="text-xl font-semibold text-white mb-6 px-4">Profile Settings</h2>
              <UserProfile 
                routing="hash"
                appearance={{
                  baseTheme: dark,
                  elements: {
                    cardBox: "shadow-none border-none",
                    card: "bg-transparent shadow-none",
                    navbar: "hidden", 
                    pageScrollBox: "p-0",
                    headerTitle: "hidden",
                    headerSubtitle: "hidden",
                    profileSection: "border-b border-white/10",
                    profileSectionTitle: "text-zinc-400",
                    profileSectionTitleText: "text-zinc-400 font-medium",
                  }
                }} 
              />
            </div>
          </div>
        )}

        {activeTab === "security" && (
          <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-6">
            <div>
              <h2 className="text-lg font-semibold text-white mb-1">Security & Privacy</h2>
              <p className="text-sm text-zinc-400 mb-6">Manage how your data is handled.</p>
            </div>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl border border-white/5">
                <div>
                  <h4 className="font-medium text-white text-sm">Local Encryption Key Storage</h4>
                  <p className="text-xs text-zinc-400 mt-1">Keys never leave your device.</p>
                </div>
                <div className="h-6 w-11 bg-blue-600 rounded-full relative cursor-pointer">
                  <div className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full" />
                </div>
              </div>
              <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl border border-white/5">
                <div>
                  <h4 className="font-medium text-white text-sm">Auto-delete documents</h4>
                  <p className="text-xs text-zinc-400 mt-1">Automatically delete scans after 30 days.</p>
                </div>
                <div className="h-6 w-11 bg-zinc-700 rounded-full relative cursor-pointer">
                  <div className="absolute left-1 top-1 w-4 h-4 bg-zinc-400 rounded-full" />
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "notifications" && (
          <div className="glass-panel p-6 rounded-2xl border border-white/10 text-center py-20">
            <Bell className="h-8 w-8 text-zinc-500 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-white">Notification Preferences</h3>
            <p className="text-sm text-zinc-400 mt-2">Notification settings will be available soon.</p>
          </div>
        )}

        {activeTab === "api" && (
          <div className="glass-panel p-6 rounded-2xl border border-white/10 text-center py-20">
            <Key className="h-8 w-8 text-zinc-500 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-white">API Access</h3>
            <p className="text-sm text-zinc-400 mt-2">API key management will be available in the Enterprise plan.</p>
          </div>
        )}
      </div>
    </div>
  );
}
