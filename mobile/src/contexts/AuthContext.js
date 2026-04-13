import React, { createContext, useContext, useEffect, useState } from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { Platform } from "react-native";

import authApi from "../services/authApi";
import studentApi from "../services/studentApi";
import { registerForPushNotifications, unregisterPushToken } from "../services/pushNotifications";

const AuthContext = createContext(null);

const initialState = {
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,
  hasProfile: false,
  applicationStatus: null,
};

export const AuthProvider = ({ children }) => {
  const [state, setState] = useState(initialState);
  const [devicePushToken, setDevicePushToken] = useState(null);

  const applyAuthState = (token, userData, isLoading = false) => {
    const hasProfile = Boolean(userData?.has_profile ?? userData?.hasProfile);
    const applicationStatus =
      userData?.application_status ?? userData?.applicationStatus ?? null;

    setState({
      user: userData || null,
      token: token || null,
      isAuthenticated: Boolean(token && userData),
      isLoading,
      hasProfile,
      applicationStatus,
    });
  };

  const clearAuthState = () => {
    setState({
      ...initialState,
      isLoading: false,
    });
  };

  const refreshUser = async () => {
    try {
      const token = await AsyncStorage.getItem("auth_token");
      if (!token) {
        clearAuthState();
        return null;
      }

      const { data } = await authApi.me();
      applyAuthState(token, data);
      return data;
    } catch (error) {
      if (error?.response?.status === 401) {
        await AsyncStorage.removeItem("auth_token");
      }
      clearAuthState();
      return null;
    }
  };

  useEffect(() => {
    const bootstrapAuth = async () => {
      setState((prev) => ({ ...prev, isLoading: true }));

      const token = await AsyncStorage.getItem("auth_token");
      if (!token) {
        clearAuthState();
        return;
      }

      await refreshUser();
    };

    bootstrapAuth();
  }, []);

  useEffect(() => {
    const registerPushToken = async () => {
      const token = await registerForPushNotifications();
      if (token) {
        setDevicePushToken({ token, platform: Platform.OS });
      }
    };

    registerPushToken();
  }, []);

  useEffect(() => {
    const syncPushToken = async () => {
      if (!state.isAuthenticated || !devicePushToken?.token) {
        return;
      }

      const cacheKey = "push_token_synced";
      const cached = await AsyncStorage.getItem(cacheKey);
      const currentValue = `${devicePushToken.platform}:${devicePushToken.token}`;
      if (cached === currentValue) {
        return;
      }

      try {
        await studentApi.savePushToken(devicePushToken);
        await AsyncStorage.setItem(cacheKey, currentValue);
      } catch {
        // Retry on next app launch/login.
      }
    };

    syncPushToken();
  }, [state.isAuthenticated, devicePushToken]);

  const login = async (token, userData) => {
    await AsyncStorage.setItem("auth_token", token);
    applyAuthState(token, userData);

    try {
      await registerForPushNotifications();
    } catch (e) {
      console.warn("Push registration failed:", e);
    }
  };

  const logout = async () => {
    try {
      await unregisterPushToken();
    } catch (e) {
      console.warn("Push unregister failed:", e);
    }
    try {
      const { Notifications } = require("expo-notifications");
      await Notifications.setBadgeCountAsync(0);
    } catch (e) {
      console.warn("Badge clear failed:", e);
    }
    try {
      await authApi.logout();
    } catch {
      // no-op
    } finally {
      await AsyncStorage.removeItem("auth_token");
      await AsyncStorage.removeItem("push_token_synced");
      clearAuthState();
    }
  };

  const completeProfile = async () => {
    setState((prev) => ({
      ...prev,
      hasProfile: true,
      user: prev.user ? { ...prev.user, has_profile: true } : prev.user,
    }));
  };

  return (
    <AuthContext.Provider
      value={{
        ...state,
        login,
        logout,
        refreshUser,
        completeProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuthContext = () => useContext(AuthContext);
