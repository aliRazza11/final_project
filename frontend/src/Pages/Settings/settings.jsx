import React, { useState } from "react";
import { ArrowLeft, User, Mail, Lock, Trash2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import ChangeUsernameModal from "../Modals/ChangeUsernameModal";
import ChangeEmailModal from "../Modals/ChangeEmailModal";
import ChangePasswordModal from "../Modals/ChangePasswordModal";
import DeleteAccountModal from "../Modals/DeleteModal";

export default function SettingsPage() {
  const navigate = useNavigate();
  const [activeModal, setActiveModal] = useState(null);

  const options = [
    {
      key: "username",
      label: "Change Username",
      description: "Update your display name.",
      icon: <User className="w-5 h-5 text-gray-600" />,
      color: "bg-gray-900 hover:bg-gray-800 text-white",
    },
    {
      key: "email",
      label: "Change Email",
      description: "Update your login email address.",
      icon: <Mail className="w-5 h-5 text-gray-600" />,
      color: "bg-gray-900 hover:bg-gray-800 text-white",
    },
    {
      key: "password",
      label: "Change Password",
      description: "Update your account password.",
      icon: <Lock className="w-5 h-5 text-gray-600" />,
      color: "bg-gray-900 hover:bg-gray-800 text-white",
    },
    {
      key: "delete",
      label: "Delete Account",
      description: "Permanently delete your account.",
      icon: <Trash2 className="w-5 h-5 text-black" />,
      color: "bg-red-600 hover:bg-red-700 text-white",
    },
  ];

  return (
    <div className="h-screen flex bg-gray-50 text-gray-900">
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-white shadow p-4 border-b border-gray-200 flex items-center gap-4">
          <button
            onClick={() => navigate("/dashboard")}
            className="p-2 rounded hover:bg-gray-100"
          >
            <ArrowLeft size={20} />
          </button>
          <h1 className="text-xl font-bold text-gray-900">Account Settings</h1>
        </header>

        {/* Options */}
        <main className="flex-1 flex items-start justify-center p-8 overflow-auto ">
          <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6 w-full max-w-2xl space-y-4">
           <div className="flex justify-center items-center">
              <h2 className=" text-lg font-bold text-gray-800 mb-4">
                Manage Your Account
              </h2>
            </div>


            <div className="divide-y divide-gray-200">
              {options.map((opt) => (
                <button
                  key={opt.key}
                  onClick={() => setActiveModal(opt.key)}
                  className={`flex items-center justify-between w-full text-left px-4 py-4 rounded-lg transition group ${opt.color} my-2`}
                >
                  <div className="flex items-center gap-3">
                    {opt.icon}
                    <div>
                      <p className="font-medium">{opt.label}</p>
                      <p className="text-sm text-gray-200">
                        {opt.description}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </main>
      </div>

      {/* Modals */}
      {activeModal === "username" && (
        <ChangeUsernameModal onClose={() => setActiveModal(null)} />
      )}
      {activeModal === "email" && (
        <ChangeEmailModal onClose={() => setActiveModal(null)} />
      )}
      {activeModal === "password" && (
        <ChangePasswordModal onClose={() => setActiveModal(null)} />
      )}
      {activeModal === "delete" && (
        <DeleteAccountModal onClose={() => setActiveModal(null)} />
      )}
    </div>
  );
}
