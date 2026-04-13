import React from 'react';
import { ScrollView, View, Text, TextInput, TouchableOpacity, StyleSheet } from 'react-native';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { useNavigation } from '@react-navigation/native';
import Toast from 'react-native-toast-message';
import { AlertCircle, CheckCircle2 } from 'lucide-react-native';
import { agentApi } from '../../services/agentApi';
import { FormField } from '../../components/ui/FormField';
import { CategoryPicker } from '../../components/agent/CategoryPicker';
import LoadingScreen from '../../components/ui/LoadingScreen';
import { useDebounce } from '../../hooks/useDebounce';
import api from '../../services/api';
import { colors, spacing, typography } from '../../theme';

const schema = z.object({
  full_name: z.string().min(3, 'Name must be at least 3 characters'),
  email: z.string().email('Invalid email address'),
  phone: z.string().regex(/^[6-9]\d{9}$/, 'Enter a valid 10-digit mobile number'),
  category: z.string().optional(),
});

export function AgentRegisterScreen() {
  const navigation = useNavigation();
  const queryClient = useQueryClient();
  
  const { data: dashboard, isLoading } = useQuery({
    queryKey: ['agent-dashboard'],
    queryFn: () => agentApi.getDashboard().then(r => r.data),
  });

  const { control, handleSubmit, reset, watch, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
    defaultValues: { full_name: '', email: '', phone: '', category: 'general' },
  });

  const emailValue = watch('email');
  const debouncedEmail = useDebounce(emailValue, 500);

  const { data: emailExists, isFetching: isCheckingEmail } = useQuery({
    queryKey: ['check-email', debouncedEmail],
    queryFn: () => api.get(`/accounts/check-email/?email=${debouncedEmail}`).then(r => r.data.exists),
    enabled: !!debouncedEmail && !errors.email,
    staleTime: 10000,
  });

  const mutation = useMutation({
    mutationFn: (data) => agentApi.registerStudent(data),
    onSuccess: (res) => {
      Toast.show({
        type: 'success',
        text1: 'Student registered',
        text2: `Verification email sent to ${res.data.email || 'the student'}`,
      });
      queryClient.invalidateQueries({ queryKey: ['agent-students'] });
      queryClient.invalidateQueries({ queryKey: ['agent-dashboard'] });
      reset();
      navigation.navigate('Students');
    },
    onError: (err) => {
      const msg = err.response?.data?.error || 'Registration failed';
      Toast.show({ type: 'error', text1: 'Error', text2: msg });
    },
  });

  if (isLoading) return <LoadingScreen />;

  // Unverified agent guard
  if (dashboard && !dashboard.agent.is_verified) {
    return (
      <View style={styles.centered}>
        <View style={styles.lockContainer}>
            <AlertCircle size={64} color="#D97706" />
            <Text style={styles.lockTitle}>Verification Pending</Text>
            <Text style={styles.lockSubtitle}>
                Your agent account is currently under review by the administration. 
                You will be able to register students once your account is verified.
            </Text>
            <TouchableOpacity 
                style={styles.backBtn}
                onPress={() => navigation.navigate('Dashboard')}
            >
                <Text style={styles.backBtnText}>Return to Dashboard</Text>
            </TouchableOpacity>
        </View>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Register New Student</Text>
      <Text style={styles.subtitle}>
        Provide the student's primary details. They will receive an invitation email to complete their profile and upload documents.
      </Text>

      <FormField label="Full Name" error={errors.full_name?.message}>
        <Controller
          control={control}
          name="full_name"
          render={({ field: { onChange, value } }) => (
            <TextInput
              style={styles.input}
              value={value}
              onChangeText={onChange}
              placeholder="Enter student's full name"
              placeholderTextColor="#94A3B8"
              autoCapitalize="words"
            />
          )}
        />
      </FormField>

      <FormField 
        label="Email Address" 
        error={errors.email?.message || (emailExists ? 'This email is already registered' : null)}
      >
        <Controller
          control={control}
          name="email"
          render={({ field: { onChange, value } }) => (
            <View>
              <TextInput
                style={[styles.input, emailExists && styles.inputError]}
                value={value}
                onChangeText={onChange}
                placeholder="student@example.com"
                placeholderTextColor="#94A3B8"
                keyboardType="email-address"
                autoCapitalize="none"
                autoCorrect={false}
              />
              {isCheckingEmail && <View style={styles.checkingBadge}><Text style={styles.checkingText}>Checking...</Text></View>}
            </View>
          )}
        />
      </FormField>

      <FormField label="Mobile Number" error={errors.phone?.message}>
        <Controller
          control={control}
          name="phone"
          render={({ field: { onChange, value } }) => (
            <TextInput
              style={styles.input}
              value={value}
              onChangeText={onChange}
              placeholder="10-digit mobile number"
              placeholderTextColor="#94A3B8"
              keyboardType="phone-pad"
              maxLength={10}
            />
          )}
        />
      </FormField>

      <FormField label="Candidate Category">
        <Controller
          control={control}
          name="category"
          render={({ field: { onChange, value } }) => (
            <CategoryPicker value={value} onChange={onChange} />
          )}
        />
      </FormField>

      <View style={styles.spacer} />

      <TouchableOpacity
        style={[styles.submitBtn, (mutation.isPending || emailExists) && styles.disabled]}
        onPress={handleSubmit((data) => mutation.mutate(data))}
        disabled={mutation.isPending || emailExists}
      >
        <Text style={styles.submitText}>
          {mutation.isPending ? 'Registering...' : 'Complete Registration'}
        </Text>
      </TouchableOpacity>
      
      <View style={styles.infoBox}>
          <CheckCircle2 size={16} color="#059669" />
          <Text style={styles.infoText}>
              Student will be added to your referral pipeline immediately.
          </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  content: {
    paddingVertical: spacing.lg,
  },
  title: {
    ...typography.h2,
    fontWeight: '900',
    color: colors.text,
    paddingHorizontal: spacing.md,
    marginBottom: 8,
  },
  subtitle: {
    ...typography.body,
    color: colors.textSecondary,
    paddingHorizontal: spacing.md,
    marginBottom: spacing.xl,
    lineHeight: 20,
  },
  input: {
    height: 52,
    backgroundColor: '#F8FAFC',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 12,
    paddingHorizontal: 16,
    fontSize: 16,
    color: colors.text,
  },
  spacer: {
    height: spacing.lg,
  },
  submitBtn: {
    backgroundColor: colors.primary,
    marginHorizontal: spacing.md,
    height: 56,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 4,
  },
  disabled: {
    opacity: 0.6,
  },
  submitText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  infoBox: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 8,
      margin: spacing.md,
      padding: spacing.md,
      backgroundColor: '#ECFDF5',
      borderRadius: 12,
  },
  infoText: {
      fontSize: 12,
      color: '#059669',
      fontWeight: '600',
  },
  centered: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
      backgroundColor: '#fff',
      padding: spacing.xl,
  },
  lockContainer: {
      alignItems: 'center',
      gap: spacing.lg,
  },
  lockTitle: {
      ...typography.h3,
      fontWeight: 'bold',
      color: colors.text,
  },
  lockSubtitle: {
      ...typography.body,
      color: colors.textSecondary,
      textAlign: 'center',
      lineHeight: 22,
  },
  backBtn: {
      marginTop: spacing.md,
      paddingHorizontal: 24,
      paddingVertical: 12,
      borderRadius: 24,
      backgroundColor: '#F1F5F9',
  },
  backBtnText: {
      color: colors.text,
      fontWeight: '700',
  },
  inputError: {
    borderColor: colors.danger,
    backgroundColor: '#FFF1F2',
  },
  checkingBadge: {
    position: 'absolute',
    right: 12,
    top: 16,
    backgroundColor: '#F1F5F9',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  checkingText: {
    fontSize: 10,
    color: '#64748B',
    fontWeight: '700',
  }
});
