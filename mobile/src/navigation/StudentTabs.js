import React from "react";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { createStackNavigator } from "@react-navigation/stack";
import { Feather } from "@expo/vector-icons";
import { useQuery } from "@tanstack/react-query";

import StudentDashboardScreen from "../screens/StudentDashboardScreen";
import DocumentListScreen from "../screens/documents/DocumentListScreen";
import DocumentUploadScreen from "../screens/documents/DocumentUploadScreen";
import OCRResultScreen from "../screens/documents/OCRResultScreen";
import DocumentViewerScreen from "../screens/documents/DocumentViewerScreen";
import ApplicationFormScreen from "../screens/application/ApplicationFormScreen";
import BranchSelectScreen from "../screens/application/BranchSelectScreen";
import SubmissionSuccessScreen from "../screens/application/SubmissionSuccessScreen";
import StatusScreen from "../screens/status/StatusScreen";
import SeatDetailsScreen from "../screens/status/SeatDetailsScreen";
import EditProfileScreen from "../screens/profile/EditProfileScreen";
import NotificationsScreen from "../screens/NotificationsScreen";
import { ROUTES } from "../constants/routes";
import studentApi from "../services/studentApi";
import { useRejectedCount } from "../hooks/useRejectedCount";
import { colors } from "../theme";

const Tab = createBottomTabNavigator();
const Stack = createStackNavigator();

const HomeStack = () => (
  <Stack.Navigator screenOptions={{ headerShown: false }}>
    <Stack.Screen name={ROUTES.HOME.DASHBOARD} component={StudentDashboardScreen} />
    <Stack.Screen name={ROUTES.PROFILE.EDIT} component={EditProfileScreen} />
    <Stack.Screen name={ROUTES.NOTIFICATIONS.LIST} component={NotificationsScreen} />
  </Stack.Navigator>
);

const DocumentsStack = () => (
  <Stack.Navigator screenOptions={{ headerShown: false }}>
    <Stack.Screen name={ROUTES.DOCUMENTS.LIST} component={DocumentListScreen} />
    <Stack.Screen name={ROUTES.DOCUMENTS.UPLOAD} component={DocumentUploadScreen} />
    <Stack.Screen name={ROUTES.DOCUMENTS.OCR_RESULT} component={OCRResultScreen} />
    <Stack.Screen name={ROUTES.DOCUMENTS.VIEWER} component={DocumentViewerScreen} />
  </Stack.Navigator>
);

const ApplicationStack = () => (
  <Stack.Navigator screenOptions={{ headerShown: false }}>
    <Stack.Screen name={ROUTES.APPLICATION.FORM} component={ApplicationFormScreen} />
    <Stack.Screen name={ROUTES.APPLICATION.BRANCH_SELECT} component={BranchSelectScreen} />
    <Stack.Screen
      name={ROUTES.APPLICATION.SUBMISSION_SUCCESS}
      component={SubmissionSuccessScreen}
    />
  </Stack.Navigator>
);

const StatusStack = () => (
  <Stack.Navigator screenOptions={{ headerShown: false }}>
    <Stack.Screen name={ROUTES.STATUS.STATUS} component={StatusScreen} />
    <Stack.Screen name={ROUTES.STATUS.SEAT_DETAILS} component={SeatDetailsScreen} />
  </Stack.Navigator>
);

export const StudentTabs = () => {
  const profileCompletionQuery = useQuery({
    queryKey: ["tab-documents-progress"],
    queryFn: async () => {
      const { data } = await studentApi.getProfileCompletion();
      return data || {};
    },
  });

  const statusQuery = useQuery({
    queryKey: ["tab-status-summary"],
    queryFn: async () => {
      const { data } = await studentApi.getStatus();
      return data || {};
    },
  });

  const { data: rejectedCount = 0 } = useRejectedCount();
  const displayRejectedCount = rejectedCount > 99 ? '99+' : rejectedCount;

  const uploadedCount = Number(profileCompletionQuery.data?.documents?.uploaded_count ?? 2);
  const requiredCount = Number(profileCompletionQuery.data?.documents?.required_count ?? 4);
  const documentsBadge = `${uploadedCount}/${requiredCount}`;
  const isActionRequired =
    Boolean(statusQuery.data?.rejected_document) ||
    Boolean(statusQuery.data?.action_required) ||
    false;

  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textSecondary,
        tabBarLabelStyle: {
          fontSize: 12,
          fontWeight: "600",
        },
        tabBarIcon: ({ color, size }) => {
          const iconMap = {
            HomeTab: "home",
            DocumentsTab: "file-text",
            ApplicationTab: "clipboard",
            StatusTab: "activity",
          };
          return <Feather name={iconMap[route.name]} size={size} color={color} />;
        },
      })}
    >
      <Tab.Screen name="HomeTab" component={HomeStack} options={{ title: "Home" }} />
      <Tab.Screen
        name="DocumentsTab"
        component={DocumentsStack}
        options={{
          title: "Documents",
          tabBarBadge: displayRejectedCount > 0 ? displayRejectedCount : documentsBadge,
          tabBarBadgeStyle: {
            backgroundColor: displayRejectedCount > 0 ? colors.danger : colors.primary,
            color: "#fff",
            fontSize: displayRejectedCount > 0 ? 11 : 10,
            fontWeight: "600",
            minWidth: displayRejectedCount > 0 ? 22 : 28,
            height: displayRejectedCount > 0 ? 18 : 16,
            borderRadius: displayRejectedCount > 0 ? 9 : 8,
          },
        }}
      />
      <Tab.Screen
        name="ApplicationTab"
        component={ApplicationStack}
        options={{ title: "Application" }}
      />
      <Tab.Screen
        name="StatusTab"
        component={StatusStack}
        options={{
          title: "Status",
          tabBarBadge: isActionRequired ? " " : undefined,
          tabBarBadgeStyle: {
            backgroundColor: colors.danger,
            width: 8,
            height: 8,
            minWidth: 8,
            borderRadius: 4,
            fontSize: 0,
            color: "transparent",
          },
        }}
      />
    </Tab.Navigator>
  );
};
