import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import Constants from 'expo-constants';
import { Platform } from 'react-native';
import api from './api';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

export async function registerForPushNotifications() {
  if (!Device.isDevice) return null;

  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;
  if (existingStatus !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }
  if (finalStatus !== 'granted') return null;

  const projectId = Constants.expoConfig?.extra?.eas?.projectId;
  const tokenData = await Notifications.getExpoPushTokenAsync({ projectId });
  const expoPushToken = tokenData.data;

  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('document_alerts', {
      name: 'Document Alerts',
      description: 'Notifications when staff request document re-uploads',
      importance: Notifications.AndroidImportance.HIGH,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: '#EF4444',
      sound: 'default',
    });
    
    await Notifications.setNotificationChannelAsync('commission_alerts', {
      name: 'Commission Alerts',
      description: 'Notifications for commission approvals and payments',
      importance: Notifications.AndroidImportance.HIGH,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: '#10B981',
      sound: 'default',
    });
    
    await Notifications.setNotificationChannelAsync('default', {
      name: 'default',
      importance: Notifications.AndroidImportance.HIGH,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: '#FF231F7C',
    });
  }

  try {
    await api.post('/notifications/device-tokens/', {
      expo_push_token: expoPushToken,
      platform: Platform.OS,
      device_name: Device.modelName,
      app_version: Constants.expoConfig?.version,
    });
  } catch (error) {
    console.error('Failed to register push token:', error);
  }

  return expoPushToken;
}

import Toast from 'react-native-toast-message';

export function setupNotificationListeners(navigationRef, queryClient) {
  Notifications.getLastNotificationResponseAsync().then((response) => {
    if (response?.notification?.request?.content?.data?.type === 'document_reupload_request') {
      const data = response.notification.request.content.data;
      if (data.document_id) {
        navigationRef.navigate('RejectedDocuments', { highlightId: data.document_id });
      } else {
        navigationRef.navigate('RejectedDocuments');
      }
    }
  });

  const receivedSub = Notifications.addNotificationReceivedListener((notification) => {
    const { title, body, data } = notification.request.content;

    if (data?.type === 'document_reupload_request') {
      Toast.show({
        type: 'error',
        text1: title || 'Document needs re-upload',
        text2: body,
        onPress: () => navigationRef.navigate('RejectedDocuments'),
        visibilityTime: 6000,
      });
      queryClient.invalidateQueries({ queryKey: ['rejected-documents'] });
      queryClient.invalidateQueries({ queryKey: ['rejected-count'] });
    }

    if (data?.type === 'commission_approved') {
      Toast.show({
        type: 'success',
        text1: title || 'Commission approved',
        text2: body,
      });
      queryClient.invalidateQueries({ queryKey: ['agent-commissions'] });
      queryClient.invalidateQueries({ queryKey: ['agent-dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['agent-commission-summary'] });
    }

    if (data?.type === 'commission_paid') {
      Toast.show({
        type: 'success',
        text1: title || 'Payment received!',
        text2: body,
        visibilityTime: 8000,
      });
      queryClient.invalidateQueries({ queryKey: ['agent-commissions'] });
      queryClient.invalidateQueries({ queryKey: ['agent-dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['agent-commission-summary'] });
    }

    if (data?.type === 'commission_rejected') {
      Toast.show({
        type: 'error',
        text1: title || 'Commission update',
        text2: body,
      });
      queryClient.invalidateQueries({ queryKey: ['agent-commissions'] });
    }
  });

  const responseSub = Notifications.addNotificationResponseReceivedListener((response) => {
    const data = response.notification.request.content.data;

    if (data?.type === 'document_reupload_request') {
      if (data.document_id) {
        navigationRef.navigate('RejectedDocuments', { highlightId: data.document_id });
      } else {
        navigationRef.navigate('RejectedDocuments');
      }
    }

    if (['commission_approved', 'commission_paid', 'commission_rejected'].includes(data?.type)) {
      navigationRef.navigate('Commissions');
    }
  });

  return () => {
    receivedSub.remove();
    responseSub.remove();
  };
}

export async function unregisterPushToken() {
  try {
    const projectId = Constants.expoConfig?.extra?.eas?.projectId;
    const tokenData = await Notifications.getExpoPushTokenAsync({ projectId });
    const expoPushToken = tokenData?.data;
    
    if (!expoPushToken) {
      return;
    }
    
    await api.delete('/notifications/device-tokens/unregister/', {
      data: { expo_push_token: expoPushToken },
    });
  } catch (error) {
    console.error('Failed to unregister push token:', error);
  }
}
