import "react-native-gesture-handler";
import React, { useCallback, useEffect, useRef, useState } from "react";
import { NavigationContainer, useNavigationContainerRef } from "@react-navigation/native";
import { SafeAreaProvider } from "react-native-safe-area-context";
import Toast from "react-native-toast-message";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { AuthProvider } from "./src/contexts/AuthContext";
import RootNavigator from "./src/navigation/RootNavigator";
import { ROUTES } from "./src/constants/routes";
import { setupNotificationListeners } from "./src/services/pushNotifications";
import { useAppIconBadge } from "./src/hooks/useAppIconBadge";

const queryClient = new QueryClient();

let Notifications = null;
try {
  Notifications = require("expo-notifications");
} catch {
  Notifications = null;
}

export default function App() {
  const navigationRef = useNavigationContainerRef();
  const [pendingOpenDocuments, setPendingOpenDocuments] = useState(false);
  const responseListenerRef = useRef(null);

  const isDocumentRejectedNotification = useCallback((response) => {
    const content = response?.notification?.request?.content || {};
    const data = content?.data || {};
    const title = String(content?.title || "").toLowerCase();
    const body = String(content?.body || "").toLowerCase();

    if (String(data?.type || "").toLowerCase() === "document_rejected") {
      return true;
    }
    if (title.includes("action required") && body.includes("rejected")) {
      return true;
    }
    return false;
  }, []);

  const canOpenDocuments = useCallback(() => {
    const rootState = navigationRef.getRootState();
    const stack = [rootState];
    while (stack.length) {
      const current = stack.pop();
      if (!current) {
        continue;
      }
      const routeNames = current.routeNames || [];
      if (routeNames.includes("DocumentsTab")) {
        return true;
      }
      const routes = current.routes || [];
      routes.forEach((route) => {
        if (route?.state) {
          stack.push(route.state);
        }
      });
    }
    return false;
  }, [navigationRef]);

  const navigateToRejectedDocs = useCallback(() => {
    if (!navigationRef.isReady() || !canOpenDocuments()) {
      return false;
    }
    navigationRef.navigate("DocumentsTab", {
      screen: ROUTES.DOCUMENTS.LIST,
      params: { highlightRejected: true },
    });
    return true;
  }, [navigationRef, canOpenDocuments]);

  useEffect(() => {
    const cleanup = setupNotificationListeners(navigationRef, queryClient);
    return cleanup;
  }, [navigationRef, queryClient]);

  useEffect(() => {
    const notificationsApi = Notifications?.default || Notifications;
    if (!notificationsApi) {
      return;
    }

    const checkInitialNotification = async () => {
      const response = await notificationsApi.getLastNotificationResponseAsync();
      if (response && isDocumentRejectedNotification(response)) {
        setPendingOpenDocuments(true);
      }
    };

    checkInitialNotification();

    responseListenerRef.current = notificationsApi.addNotificationResponseReceivedListener(
      (response) => {
        if (isDocumentRejectedNotification(response)) {
          const navigated = navigateToRejectedDocs();
          if (!navigated) {
            setPendingOpenDocuments(true);
          }
        }
      }
    );

    return () => {
      if (responseListenerRef.current) {
        responseListenerRef.current.remove();
      }
    };
  }, [isDocumentRejectedNotification, navigateToRejectedDocs]);

  const processPendingNavigation = useCallback(() => {
    if (!pendingOpenDocuments) {
      return;
    }
    const ok = navigateToRejectedDocs();
    if (ok) {
      setPendingOpenDocuments(false);
    }
  }, [pendingOpenDocuments, navigateToRejectedDocs]);

  const AppInner = useCallback(() => {
    useAppIconBadge();
    return (
      <NavigationContainer
        ref={navigationRef}
        onReady={processPendingNavigation}
        onStateChange={processPendingNavigation}
      >
        <RootNavigator />
      </NavigationContainer>
    );
  }, [navigationRef, processPendingNavigation]);

  return (
    <SafeAreaProvider>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <AppInner />
        </AuthProvider>
      </QueryClientProvider>
      <Toast />
    </SafeAreaProvider>
  );
}
