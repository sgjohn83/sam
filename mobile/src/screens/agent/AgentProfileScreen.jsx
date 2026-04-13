import React, { useState, useEffect } from 'react';
import { ScrollView, View, Text, StyleSheet, TextInput, TouchableOpacity } from 'react-native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import Toast from 'react-native-toast-message';
import { User, Landmark, CreditCard, ShieldCheck, Calendar, Percent } from 'lucide-react-native';
import { agentApi } from '../../services/agentApi';
import { FormField } from '../../components/ui/FormField';
import LoadingScreen from '../../components/ui/LoadingScreen';
import { Card } from '../../components/ui/Card';
import { colors, spacing, typography } from '../../theme';

const profileSchema = z.object({
  agency_name: z.string().min(2, 'Agency name is required'),
  contact_phone: z.string().regex(/^[6-9]\d{9}$/, 'Enter a valid 10-digit mobile number'),
  bank_account_name: z.string().min(2, 'Account holder name is required').optional().or(z.literal('')),
  bank_account_number: z.string().regex(/^\d{8,18}$/, 'Account number must be 8-18 digits').optional().or(z.literal('')),
  bank_ifsc: z.string().regex(/^[A-Z]{4}0[A-Z0-9]{6}$/, 'Invalid IFSC format (e.g. SBIN0012345)').optional().or(z.literal('')),
  pan_number: z.string().regex(/^[A-Z]{5}[0-9]{4}[A-Z]$/, 'Invalid PAN format').optional().or(z.literal('')),
});

export function AgentProfileScreen() {
  const queryClient = useQueryClient();
  const [activeSection, setActiveSection] = useState(null);

  const { data: profile, isLoading } = useQuery({
    queryKey: ['agent-profile'],
    queryFn: () => agentApi.getProfile().then(r => r.data),
  });

  const { control, handleSubmit, reset, formState: { errors, isDirty } } = useForm({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      agency_name: '',
      contact_phone: '',
      bank_account_name: '',
      bank_account_number: '',
      bank_ifsc: '',
      pan_number: '',
    },
  });

  useEffect(() => {
    if (profile) {
      reset({
        agency_name: profile.agency_name || '',
        contact_phone: profile.contact_phone || '',
        bank_account_name: profile.bank_account_name || '',
        bank_account_number: profile.bank_account_number || '',
        bank_ifsc: profile.bank_ifsc || '',
        pan_number: profile.pan_number || '',
      });
    }
  }, [profile, reset]);

  const updateMutation = useMutation({
    mutationFn: (data) => agentApi.updateProfile(data),
    onSuccess: () => {
      Toast.show({ type: 'success', text1: 'Profile Updated' });
      queryClient.invalidateQueries({ queryKey: ['agent-profile'] });
      queryClient.invalidateQueries({ queryKey: ['agent-completion'] });
      setActiveSection(null);
    },
    onError: (err) => {
      const msg = err.response?.data?.error || 'Update failed';
      Toast.show({ type: 'error', text1: 'Error', text2: msg });
    },
  });

  if (isLoading) return <LoadingScreen />;

  const onSaveSection = (data) => {
    // Only send fields related to the active section if we wanted to be granular, 
    // but a full patch of dirty fields is also fine.
    updateMutation.mutate(data);
  };

  const SectionHeader = ({ icon: Icon, title, sectionKey }) => (
    <View style={styles.sectionHeader}>
      <View style={styles.sectionTitleRow}>
        <Icon size={20} color={colors.primary} />
        <Text style={styles.sectionTitle}>{title}</Text>
      </View>
      {activeSection !== sectionKey ? (
        <TouchableOpacity onPress={() => setActiveSection(sectionKey)}>
          <Text style={styles.editBtn}>Edit</Text>
        </TouchableOpacity>
      ) : (
        <TouchableOpacity onPress={handleSubmit(onSaveSection)}>
            <Text style={[styles.saveBtn, updateMutation.isPending && { opacity: 0.5 }]}>
                {updateMutation.isPending ? '...' : 'Save'}
            </Text>
        </TouchableOpacity>
      )}
    </View>
  );

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <View style={[styles.statusBadge, { backgroundColor: profile.is_verified ? '#ECFDF5' : '#FEF3C7' }]}>
            <ShieldCheck size={14} color={profile.is_verified ? '#059669' : '#D97706'} />
            <Text style={[styles.statusText, { color: profile.is_verified ? '#059669' : '#D97706' }]}>
                {profile.is_verified ? 'Verified Partner' : 'Verification Pending'}
            </Text>
        </View>
        <Text style={styles.userName}>{profile.full_name}</Text>
        <Text style={styles.userEmail}>{profile.email}</Text>
      </View>

      {/* Section 1: Basic Info */}
      <Card style={styles.sectionCard}>
        <SectionHeader icon={User} title="Business Information" sectionKey="basic" />
        <View style={styles.fieldsContainer}>
          <ReadOnlyOrInput
            label="Agency Name"
            name="agency_name"
            control={control}
            error={errors.agency_name?.message}
            editing={activeSection === 'basic'}
            value={profile.agency_name}
          />
          <ReadOnlyOrInput
            label="Contact Phone"
            name="contact_phone"
            control={control}
            error={errors.contact_phone?.message}
            editing={activeSection === 'basic'}
            value={profile.contact_phone}
            keyboardType="phone-pad"
          />
        </View>
      </Card>

      {/* Section 2: Bank Details */}
      <Card style={styles.sectionCard}>
        <SectionHeader icon={Landmark} title="Banking Details" sectionKey="bank" />
        <View style={styles.fieldsContainer}>
          <ReadOnlyOrInput
            label="Account Holder"
            name="bank_account_name"
            control={control}
            error={errors.bank_account_name?.message}
            editing={activeSection === 'bank'}
            value={profile.bank_account_name}
          />
          <ReadOnlyOrInput
            label="Account Number"
            name="bank_account_number"
            control={control}
            error={errors.bank_account_number?.message}
            editing={activeSection === 'bank'}
            value={profile.bank_account_number}
            mask
          />
          <ReadOnlyOrInput
            label="IFSC Code"
            name="bank_ifsc"
            control={control}
            error={errors.bank_ifsc?.message}
            editing={activeSection === 'bank'}
            value={profile.bank_ifsc}
            autoCapitalize="characters"
          />
        </View>
      </Card>

      {/* Section 3: PAN */}
      <Card style={styles.sectionCard}>
        <SectionHeader icon={CreditCard} title="Tax Information" sectionKey="tax" />
        <View style={styles.fieldsContainer}>
          <ReadOnlyOrInput
            label="PAN Number"
            name="pan_number"
            control={control}
            error={errors.pan_number?.message}
            editing={activeSection === 'tax'}
            value={profile.pan_number}
            autoCapitalize="characters"
          />
        </View>
      </Card>

      {/* Section 4: Read Only Info */}
      <Card style={styles.sectionCard}>
        <View style={styles.sectionHeader}>
            <View style={styles.sectionTitleRow}>
                <Percent size={20} color="#94A3B8" />
                <Text style={styles.sectionTitle}>Commission Policy</Text>
            </View>
        </View>
        <View style={styles.adminInfo}>
            <View style={styles.adminRow}>
                <Text style={styles.adminLabel}>Base Rate</Text>
                <Text style={styles.adminValue}>{profile.commission_rate}% per admission</Text>
            </View>
            <View style={styles.adminRow}>
                <Calendar size={14} color="#94A3B8" />
                <Text style={styles.adminDate}>Partner since {new Date(profile.created_at).toLocaleDateString()}</Text>
            </View>
        </View>
      </Card>

      <TouchableOpacity 
        style={styles.logoutBtn}
        onPress={() => { /* Handle logout */ }}
      >
          <Text style={styles.logoutText}>Log Out Account</Text>
      </TouchableOpacity>

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

const ReadOnlyOrInput = ({ label, name, control, error, editing, value, mask, ...props }) => {
  if (!editing) {
    let displayValue = value || 'Not provided';
    if (mask && value && value.length > 4) {
      displayValue = 'X'.repeat(value.length - 4) + value.slice(-4);
    }
    return (
      <View style={styles.field}>
        <Text style={styles.fieldLabel}>{label}</Text>
        <Text style={[styles.fieldValue, !value && { color: '#CBD5E1', fontStyle: 'italic' }]}>
            {displayValue}
        </Text>
      </View>
    );
  }

  return (
    <FormField label={label} error={error}>
        <Controller
            control={control}
            name={name}
            render={({ field: { onChange, value } }) => (
                <TextInput
                    style={styles.input}
                    value={value}
                    onChangeText={onChange}
                    placeholder={`Enter ${label}`}
                    placeholderTextColor="#94A3B8"
                    {...props}
                />
            )}
        />
    </FormField>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  content: {
    paddingBottom: spacing.xl,
  },
  header: {
    padding: spacing.xl,
    alignItems: 'center',
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    marginBottom: spacing.md,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '800',
    textTransform: 'uppercase',
  },
  userName: {
    ...typography.h3,
    fontWeight: '900',
    color: colors.text,
  },
  userEmail: {
    ...typography.body,
    color: colors.textSecondary,
    marginTop: 2,
  },
  sectionCard: {
    margin: spacing.md,
    marginBottom: 0,
    padding: 0,
    overflow: 'hidden',
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
    backgroundColor: '#FCFDFF',
  },
  sectionTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  sectionTitle: {
    ...typography.h5,
    fontWeight: '800',
    color: colors.text,
  },
  editBtn: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.primary,
  },
  saveBtn: {
    fontSize: 14,
    fontWeight: '900',
    color: '#059669',
  },
  fieldsContainer: {
    padding: spacing.md,
  },
  field: {
    marginBottom: spacing.md,
  },
  fieldLabel: {
    fontSize: 10,
    fontWeight: '700',
    color: '#94A3B8',
    textTransform: 'uppercase',
    marginBottom: 4,
  },
  fieldValue: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.text,
  },
  input: {
    height: 48,
    backgroundColor: '#F8FAFC',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 10,
    paddingHorizontal: 12,
    fontSize: 15,
    color: colors.text,
  },
  adminInfo: {
      padding: spacing.md,
  },
  adminRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: spacing.sm,
  },
  adminLabel: {
      fontSize: 14,
      color: colors.textSecondary,
  },
  adminValue: {
      fontSize: 14,
      fontWeight: 'bold',
      color: colors.primary,
  },
  adminDate: {
      fontSize: 12,
      color: '#94A3B8',
      flex: 1,
      marginLeft: 8,
  },
  logoutBtn: {
      margin: spacing.xl,
      height: 52,
      borderRadius: 12,
      borderWidth: 1,
      borderColor: '#FEE2E2',
      backgroundColor: '#fff',
      justifyContent: 'center',
      alignItems: 'center',
  },
  logoutText: {
      color: colors.danger,
      fontWeight: '700',
      fontSize: 15,
  }
});
