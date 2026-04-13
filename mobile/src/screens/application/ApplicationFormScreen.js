import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { useFocusEffect } from "@react-navigation/native";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Controller, useForm } from "react-hook-form";
import Toast from "react-native-toast-message";
import { Feather } from "@expo/vector-icons";

import Header from "../../components/layout/Header";
import ScreenWrapper from "../../components/layout/ScreenWrapper";
import SubmitConfirmModal from "../../components/SubmitConfirmModal";
import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";
import Input from "../../components/ui/Input";
import Select from "../../components/ui/Select";
import Spinner from "../../components/ui/Spinner";
import INDIAN_STATES from "../../constants/indianStates";
import { ROUTES } from "../../constants/routes";
import { useAutofill } from "../../hooks/useAutofill";
import studentApi from "../../services/studentApi";
import { colors, fontSize, spacing } from "../../theme";

const DRAFT_KEY = "application_form_draft_v1";

const defaultValues = {
  fullName: "",
  dateOfBirth: "",
  gender: "",
  mobile: "",
  aadharNumber: "",
  address: "",
  category: "",
  domicileState: "",
  sscHallTicket: "",
  sscSchoolName: "",
  sscBoard: "",
  sscYear: "",
  sscGpa: "",
  sscSubjectsText: "",
  interHallTicket: "",
  interCollegeName: "",
  interGroup: "",
  interYear: "",
  interTotalMarks: "",
  interSubjectsFirstYear: "",
  interSubjectsSecondYear: "",
  examName: "",
  entranceHallTicket: "",
  entranceRank: "",
  categoryRank: "",
};

const GENDER_OPTIONS = [
  { label: "Male", value: "Male" },
  { label: "Female", value: "Female" },
  { label: "Other", value: "Other" },
];

const CATEGORY_OPTIONS = [
  { label: "General", value: "General" },
  { label: "OBC", value: "OBC" },
  { label: "SC", value: "SC" },
  { label: "ST", value: "ST" },
];

const STATE_OPTIONS = INDIAN_STATES.map((state) => ({ label: state, value: state }));

const SOURCE_MAP = {
  fullName: "Aadhar Card",
  dateOfBirth: "Aadhar Card",
  gender: "Aadhar Card",
  mobile: "Aadhar Card",
  aadharNumber: "Aadhar Card",
  address: "Aadhar Card",
  category: "Rank Card",
  domicileState: "Profile",
  sscHallTicket: "10th Marksheet",
  sscSchoolName: "10th Marksheet",
  sscBoard: "10th Marksheet",
  sscYear: "10th Marksheet",
  sscGpa: "10th Marksheet",
  sscSubjectsText: "10th Marksheet",
  interHallTicket: "12th Marksheet",
  interCollegeName: "12th Marksheet",
  interGroup: "12th Marksheet",
  interYear: "12th Marksheet",
  interTotalMarks: "12th Marksheet",
  interSubjectsFirstYear: "12th Marksheet",
  interSubjectsSecondYear: "12th Marksheet",
  examName: "Rank Card",
  entranceHallTicket: "Rank Card",
  entranceRank: "Rank Card",
  categoryRank: "Rank Card",
};

const formatSubjects = (subjects) => {
  if (!subjects) {
    return "";
  }
  if (Array.isArray(subjects)) {
    return subjects
      .map((entry) => {
        if (typeof entry === "string") {
          return entry;
        }
        if (entry?.name && entry?.grade) {
          return `${entry.name}: ${entry.grade}`;
        }
        if (entry?.name) {
          return entry.name;
        }
        return JSON.stringify(entry);
      })
      .join("\n");
  }
  return String(subjects);
};

const mapAutofillToValues = (autofill) => {
  const profile = autofill?.profile_fields || {};
  const academic = autofill?.academic_fields || {};
  const lowConfidence = new Set(
    (autofill?.confidence_summary?.low_confidence_fields || []).map((value) => String(value))
  );

  const formValues = {
    ...defaultValues,
    fullName: profile.full_name || "",
    dateOfBirth: profile.date_of_birth || "",
    gender: profile.gender || "",
    mobile: profile.mobile_number || "",
    aadharNumber: profile.aadhar_number || "",
    address:
      profile.address && typeof profile.address === "object"
        ? [profile.address.street, profile.address.city, profile.address.state, profile.address.pincode]
            .filter(Boolean)
            .join(", ")
        : "",
    category: profile.category || "",
    domicileState: profile.domicile_state || "",
    sscHallTicket: academic.ssc_hall_ticket || "",
    sscSchoolName: academic.ssc_school_name || "",
    sscBoard: academic.ssc_board || "",
    sscYear: academic.ssc_year || academic.ssc_year_of_passing || "",
    sscGpa: academic.ssc_gpa || "",
    sscSubjectsText: formatSubjects(academic.ssc_subjects),
    interHallTicket: academic.inter_hall_ticket || "",
    interCollegeName: academic.inter_college_name || "",
    interGroup: academic.inter_group || "",
    interYear: academic.inter_year || academic.inter_year_of_passing || "",
    interTotalMarks: academic.inter_total_marks || "",
    interSubjectsFirstYear: formatSubjects(academic.inter_subjects?.first_year),
    interSubjectsSecondYear: formatSubjects(academic.inter_subjects?.second_year),
    examName: academic.entrance_exam || academic.entrance_exam_name || "",
    entranceHallTicket: academic.rank_hall_ticket || "",
    entranceRank: academic.entrance_rank || "",
    categoryRank: academic.category_rank || "",
  };

  const autofilledFields = new Set(
    Object.entries(formValues)
      .filter(([, value]) => String(value || "").trim() !== "")
      .map(([key]) => key)
  );

  const lowConfidenceFields = new Set();
  lowConfidence.forEach((field) => {
    const map = {
      full_name: "fullName",
      date_of_birth: "dateOfBirth",
      gender: "gender",
      mobile_number: "mobile",
      aadhar_number: "aadharNumber",
      address: "address",
      category: "category",
      domicile_state: "domicileState",
      ssc_hall_ticket: "sscHallTicket",
      ssc_school_name: "sscSchoolName",
      ssc_board: "sscBoard",
      ssc_year: "sscYear",
      ssc_gpa: "sscGpa",
      ssc_subjects: "sscSubjectsText",
      inter_hall_ticket: "interHallTicket",
      inter_college_name: "interCollegeName",
      inter_group: "interGroup",
      inter_year: "interYear",
      inter_total_marks: "interTotalMarks",
      inter_subjects: "interSubjectsFirstYear",
      entrance_exam_name: "examName",
      rank_hall_ticket: "entranceHallTicket",
      entrance_rank: "entranceRank",
      category_rank: "categoryRank",
    };
    if (map[field]) {
      lowConfidenceFields.add(map[field]);
      if (field === "inter_subjects") {
        lowConfidenceFields.add("interSubjectsSecondYear");
      }
    }
  });

  return { formValues, autofilledFields, lowConfidenceFields };
};

const FieldIndicator = ({ field, value, autofilledFields, lowConfidenceFields }) => {
  const stringValue = String(value || "").trim();
  if (!stringValue) {
    return <Text style={styles.indicatorMissing}>Could not be extracted - please fill manually</Text>;
  }
  if (lowConfidenceFields.has(field)) {
    return <Text style={styles.indicatorLow}>Please verify - low confidence</Text>;
  }
  if (autofilledFields.has(field)) {
    return <Text style={styles.indicatorAuto}>Auto-filled from {SOURCE_MAP[field]}</Text>;
  }
  return null;
};

const SectionHeader = ({ title }) => <Text style={styles.sectionTitle}>{title}</Text>;

const REQUIRED_DOCUMENT_TYPES = ["aadhar", "marksheet_10", "marksheet_12", "rank_card"];

const getStatusesFromDocumentsMap = (documentsMap) => {
  if (!documentsMap || typeof documentsMap !== "object") {
    return [];
  }

  return REQUIRED_DOCUMENT_TYPES
    .map((docType) => documentsMap[docType])
    .filter(Boolean)
    .map((doc) => String(doc.status || "").toLowerCase());
};

const getUploadedCountFromDocumentsMap = (documentsMap) => {
  if (!documentsMap || typeof documentsMap !== "object") {
    return 0;
  }
  return REQUIRED_DOCUMENT_TYPES.reduce((count, docType) => {
    const doc = documentsMap[docType];
    if (!doc) {
      return count;
    }
    return doc.uploaded ? count + 1 : count;
  }, 0);
};

const isFilled = (value) => String(value ?? "").trim().length > 0;

const ApplicationFormScreen = ({ navigation }) => {
  const autofillQuery = useAutofill();
  const applicationQuery = useQuery({
    queryKey: ["student-application"],
    queryFn: async () => {
      const { data } = await studentApi.getApplication();
      return data || {};
    },
  });
  const completionQuery = useQuery({
    queryKey: ["student-profile-completion"],
    queryFn: async () => {
      const { data } = await studentApi.getProfileCompletion();
      return data || {};
    },
    retry: 0,
  });

  const [draftLoaded, setDraftLoaded] = useState(false);
  const [draftValues, setDraftValues] = useState(null);
  const [initialized, setInitialized] = useState(false);
  const [autofilledFields, setAutofilledFields] = useState(new Set());
  const [lowConfidenceFields, setLowConfidenceFields] = useState(new Set());
  const [showSscSubjects, setShowSscSubjects] = useState(false);
  const [showInterSubjects, setShowInterSubjects] = useState(false);
  const [declarationChecked, setDeclarationChecked] = useState(false);
  const [showSubmitModal, setShowSubmitModal] = useState(false);

  const { control, reset, watch, getValues } = useForm({ defaultValues });
  const values = watch();

  useFocusEffect(
    useCallback(() => {
      applicationQuery.refetch();
      completionQuery.refetch();
      autofillQuery.refetch();
    }, [applicationQuery, completionQuery, autofillQuery])
  );

  useEffect(() => {
    const loadDraft = async () => {
      try {
        const raw = await AsyncStorage.getItem(DRAFT_KEY);
        if (raw) {
          const parsed = JSON.parse(raw);
          setDraftValues(parsed);
        }
      } catch {
        // ignore invalid draft
      } finally {
        setDraftLoaded(true);
      }
    };
    loadDraft();
  }, []);

  useEffect(() => {
    if (initialized || !draftLoaded || autofillQuery.isLoading) {
      return;
    }

    const mapped = mapAutofillToValues(autofillQuery.data || {});
    const merged = {
      ...mapped.formValues,
      ...(draftValues || {}),
    };
    reset(merged);
    setAutofilledFields(mapped.autofilledFields);
    setLowConfidenceFields(mapped.lowConfidenceFields);
    setInitialized(true);
  }, [initialized, draftLoaded, autofillQuery.isLoading, autofillQuery.data, draftValues, reset]);

  const onSaveDraft = async () => {
    try {
      await AsyncStorage.setItem(DRAFT_KEY, JSON.stringify(getValues()));
      Toast.show({
        type: "success",
        text1: "Draft saved",
      });
    } catch {
      Toast.show({
        type: "error",
        text1: "Failed to save draft",
      });
    }
  };

  const submitMutation = useMutation({
    mutationFn: () => studentApi.submitApplication(),
    onSuccess: () => {
      setShowSubmitModal(false);
      Toast.show({
        type: "success",
        text1: "Application submitted successfully",
      });
      setDeclarationChecked(false);
      applicationQuery.refetch();
      completionQuery.refetch();
      navigation.navigate(ROUTES.APPLICATION.SUBMISSION_SUCCESS, {
        applicationNumber: applicationQuery.data?.application_number,
      });
    },
    onError: (error) => {
      setShowSubmitModal(false);
      const message =
        error?.response?.data?.error ||
        error?.response?.data?.detail ||
        "Failed to submit application";
      Toast.show({
        type: "error",
        text1: message,
      });
    },
  });

  const branchPreferences = useMemo(() => {
    const branchList = applicationQuery.data?.branch_preferences || [];
    if (!Array.isArray(branchList)) {
      return [];
    }
    return branchList;
  }, [applicationQuery.data]);

  const autofillDocumentsMap = autofillQuery.data?.documents_status || {};
  const fallbackStatuses = getStatusesFromDocumentsMap(autofillDocumentsMap);
  const fallbackUploadedCount = getUploadedCountFromDocumentsMap(autofillDocumentsMap);

  const completionData = completionQuery.data || {};
  const completionDocuments = completionData.documents || {};

  const localProfileComplete = [
    values.fullName,
    values.dateOfBirth,
    values.gender,
    values.mobile,
    values.address,
    values.category,
    values.domicileState,
  ].every(isFilled);

  const completionProfileFlag =
    completionData.is_complete ??
    completionData.profile_complete ??
    completionData.profile?.is_complete;

  const profileComplete =
    typeof completionProfileFlag === "boolean"
      ? completionProfileFlag
      : localProfileComplete;

  const completionDocumentsComplete =
    completionData.documents_complete ?? completionDocuments.is_complete;

  const documentsComplete =
    typeof completionDocumentsComplete === "boolean"
      ? completionDocumentsComplete
      : fallbackUploadedCount >= REQUIRED_DOCUMENT_TYPES.length;

  const statusesFromCompletion = Array.isArray(completionDocuments.items)
    ? completionDocuments.items.map((item) => String(item?.status || "").toLowerCase())
    : [];

  const effectiveStatuses =
    statusesFromCompletion.length > 0 ? statusesFromCompletion : fallbackStatuses;

  const rejectedCount = effectiveStatuses.filter((status) => status === "rejected").length;
  const processingCount = effectiveStatuses.filter((status) => status === "processing").length;

  const noRejectedDocuments = rejectedCount === 0;
  const noProcessingDocuments = processingCount === 0;
  const hasBranchPreferences = branchPreferences.length >= 1;
  const isApplicationLocked =
    Boolean(applicationQuery.data?.status) && applicationQuery.data?.status !== "draft";
  const isDraftAndEditable =
    applicationQuery.data?.status === "draft" &&
    Boolean(applicationQuery.data?.can_edit ?? true);

  const checklist = [
    {
      key: "profile",
      label: "Profile complete",
      passed: profileComplete,
      subLabel: profileComplete ? "Profile is complete" : "Complete your profile",
    },
    {
      key: "uploaded",
      label: "All 4 documents uploaded",
      passed: documentsComplete,
      subLabel: documentsComplete
        ? "All required documents uploaded"
        : `${Math.min(fallbackUploadedCount, 4)}/4 uploaded`,
    },
    {
      key: "rejected",
      label: "No rejected documents",
      passed: noRejectedDocuments,
      subLabel:
        rejectedCount === 0
          ? "No rejected documents"
          : `${rejectedCount} document${rejectedCount > 1 ? "s" : ""} rejected`,
    },
    {
      key: "processing",
      label: "No documents processing",
      passed: noProcessingDocuments,
      subLabel:
        processingCount === 0
          ? "No documents processing"
          : `${processingCount} document${processingCount > 1 ? "s are" : " is"} still processing`,
    },
    {
      key: "branches",
      label: "Branch preferences set",
      passed: hasBranchPreferences,
      subLabel: `${branchPreferences.length} branch preference${
        branchPreferences.length === 1 ? "" : "s"
      } selected`,
    },
    {
      key: "declaration",
      label: "Declaration checkbox",
      passed: declarationChecked,
      subLabel: declarationChecked ? "Declaration accepted" : "Please accept declaration",
    },
  ];

  const canSubmit = checklist.every((item) => item.passed);
  const finalCanSubmit = canSubmit && isDraftAndEditable;

  if (autofillQuery.isLoading || !draftLoaded || !initialized) {
    return <Spinner fullScreen size="large" />;
  }

  return (
    <ScreenWrapper scroll={false} padded={false}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          <Header title="Application Form" subtitle="Review OCR pre-filled details and edit if needed" />
          {isApplicationLocked ? (
            <Card style={styles.lockBanner}>
              <Text style={styles.lockBannerText}>Application submitted. Awaiting verification.</Text>
            </Card>
          ) : null}

          <View
            pointerEvents={isApplicationLocked ? "none" : "auto"}
            style={isApplicationLocked ? styles.readOnlyWrap : null}
          >
            <Card style={styles.sectionCard}>
              <SectionHeader title="Section 1: Personal Details" />

            <Input control={control} name="fullName" label="Full Name" />
            <FieldIndicator
              field="fullName"
              value={values.fullName}
              autofilledFields={autofilledFields}
              lowConfidenceFields={lowConfidenceFields}
            />

            <Input control={control} name="dateOfBirth" label="Date of Birth" placeholder="YYYY-MM-DD" />
            <FieldIndicator
              field="dateOfBirth"
              value={values.dateOfBirth}
              autofilledFields={autofilledFields}
              lowConfidenceFields={lowConfidenceFields}
            />

            <Controller
              control={control}
              name="gender"
              render={({ field: { value, onChange } }) => (
                <Select
                  label="Gender"
                  options={GENDER_OPTIONS}
                  value={value}
                  onChange={onChange}
                  placeholder="Select gender"
                />
              )}
            />
            <FieldIndicator
              field="gender"
              value={values.gender}
              autofilledFields={autofilledFields}
              lowConfidenceFields={lowConfidenceFields}
            />

            <Input control={control} name="mobile" label="Mobile" keyboardType="phone-pad" />
            <FieldIndicator
              field="mobile"
              value={values.mobile}
              autofilledFields={autofilledFields}
              lowConfidenceFields={lowConfidenceFields}
            />

            <Input control={control} name="aadharNumber" label="Aadhar Number" />
            <FieldIndicator
              field="aadharNumber"
              value={values.aadharNumber}
              autofilledFields={autofilledFields}
              lowConfidenceFields={lowConfidenceFields}
            />

            <Input control={control} name="address" label="Address" multiline />
            <FieldIndicator
              field="address"
              value={values.address}
              autofilledFields={autofilledFields}
              lowConfidenceFields={lowConfidenceFields}
            />

            <Controller
              control={control}
              name="category"
              render={({ field: { value, onChange } }) => (
                <Select
                  label="Category"
                  options={CATEGORY_OPTIONS}
                  value={value}
                  onChange={onChange}
                  placeholder="Select category"
                />
              )}
            />
            <FieldIndicator
              field="category"
              value={values.category}
              autofilledFields={autofilledFields}
              lowConfidenceFields={lowConfidenceFields}
            />

            <Controller
              control={control}
              name="domicileState"
              render={({ field: { value, onChange } }) => (
                <Select
                  label="Domicile State"
                  options={STATE_OPTIONS}
                  value={value}
                  onChange={onChange}
                  placeholder="Select domicile state"
                />
              )}
            />
            <FieldIndicator
              field="domicileState"
              value={values.domicileState}
              autofilledFields={autofilledFields}
              lowConfidenceFields={lowConfidenceFields}
            />
            </Card>

            <Card style={styles.sectionCard}>
              <SectionHeader title="Section 2: SSC (10th) Details" />
            <Input control={control} name="sscHallTicket" label="Hall Ticket No" />
            <FieldIndicator
              field="sscHallTicket"
              value={values.sscHallTicket}
              autofilledFields={autofilledFields}
              lowConfidenceFields={lowConfidenceFields}
            />
            <Input control={control} name="sscSchoolName" label="School Name" />
            <FieldIndicator
              field="sscSchoolName"
              value={values.sscSchoolName}
              autofilledFields={autofilledFields}
              lowConfidenceFields={lowConfidenceFields}
            />
            <Input control={control} name="sscBoard" label="Board" />
            <FieldIndicator
              field="sscBoard"
              value={values.sscBoard}
              autofilledFields={autofilledFields}
              lowConfidenceFields={lowConfidenceFields}
            />
            <Input control={control} name="sscYear" label="Year of Passing" keyboardType="number-pad" />
            <FieldIndicator
              field="sscYear"
              value={values.sscYear}
              autofilledFields={autofilledFields}
              lowConfidenceFields={lowConfidenceFields}
            />
            <Input control={control} name="sscGpa" label="GPA" keyboardType="numeric" />
            <FieldIndicator
              field="sscGpa"
              value={values.sscGpa}
              autofilledFields={autofilledFields}
              lowConfidenceFields={lowConfidenceFields}
            />

            <Pressable style={styles.expandHeader} onPress={() => setShowSscSubjects((v) => !v)}>
              <Text style={styles.expandTitle}>Subjects (expandable list)</Text>
              <Feather name={showSscSubjects ? "chevron-up" : "chevron-down"} size={18} color={colors.text} />
            </Pressable>
            {showSscSubjects ? (
              <Controller
                control={control}
                name="sscSubjectsText"
                render={({ field: { value, onChange } }) => (
                  <TextInput
                    style={styles.subjectInput}
                    multiline
                    value={value}
                    onChangeText={onChange}
                    placeholder="Subject list (one per line)"
                    placeholderTextColor={colors.textSecondary}
                  />
                )}
              />
            ) : null}
            <FieldIndicator
              field="sscSubjectsText"
              value={values.sscSubjectsText}
              autofilledFields={autofilledFields}
              lowConfidenceFields={lowConfidenceFields}
            />
            </Card>

            <Card style={styles.sectionCard}>
              <SectionHeader title="Section 3: Intermediate (12th) Details" />
            <Input control={control} name="interHallTicket" label="Hall Ticket No" />
            <FieldIndicator
              field="interHallTicket"
              value={values.interHallTicket}
              autofilledFields={autofilledFields}
              lowConfidenceFields={lowConfidenceFields}
            />
            <Input control={control} name="interCollegeName" label="College Name" />
            <FieldIndicator
              field="interCollegeName"
              value={values.interCollegeName}
              autofilledFields={autofilledFields}
              lowConfidenceFields={lowConfidenceFields}
            />
            <Input control={control} name="interGroup" label="Group" />
            <FieldIndicator
              field="interGroup"
              value={values.interGroup}
              autofilledFields={autofilledFields}
              lowConfidenceFields={lowConfidenceFields}
            />
            <Input control={control} name="interYear" label="Year of Passing" keyboardType="number-pad" />
            <FieldIndicator
              field="interYear"
              value={values.interYear}
              autofilledFields={autofilledFields}
              lowConfidenceFields={lowConfidenceFields}
            />
            <Input control={control} name="interTotalMarks" label="Total Marks" keyboardType="numeric" />
            <FieldIndicator
              field="interTotalMarks"
              value={values.interTotalMarks}
              autofilledFields={autofilledFields}
              lowConfidenceFields={lowConfidenceFields}
            />

            <Pressable style={styles.expandHeader} onPress={() => setShowInterSubjects((v) => !v)}>
              <Text style={styles.expandTitle}>Subjects (expandable, year-wise)</Text>
              <Feather name={showInterSubjects ? "chevron-up" : "chevron-down"} size={18} color={colors.text} />
            </Pressable>
            {showInterSubjects ? (
              <>
                <Text style={styles.subLabel}>First Year Subjects</Text>
                <Controller
                  control={control}
                  name="interSubjectsFirstYear"
                  render={({ field: { value, onChange } }) => (
                    <TextInput
                      style={styles.subjectInput}
                      multiline
                      value={value}
                      onChangeText={onChange}
                      placeholder="First year subjects"
                      placeholderTextColor={colors.textSecondary}
                    />
                  )}
                />
                <Text style={styles.subLabel}>Second Year Subjects</Text>
                <Controller
                  control={control}
                  name="interSubjectsSecondYear"
                  render={({ field: { value, onChange } }) => (
                    <TextInput
                      style={styles.subjectInput}
                      multiline
                      value={value}
                      onChangeText={onChange}
                      placeholder="Second year subjects"
                      placeholderTextColor={colors.textSecondary}
                    />
                  )}
                />
              </>
            ) : null}
            <FieldIndicator
              field="interSubjectsFirstYear"
              value={`${values.interSubjectsFirstYear}${values.interSubjectsSecondYear}`}
              autofilledFields={autofilledFields}
              lowConfidenceFields={lowConfidenceFields}
            />
            </Card>

            <Card style={styles.sectionCard}>
              <SectionHeader title="Section 4: Entrance Exam" />
            <Input control={control} name="examName" label="Exam Name" />
            <FieldIndicator
              field="examName"
              value={values.examName}
              autofilledFields={autofilledFields}
              lowConfidenceFields={lowConfidenceFields}
            />
            <Input control={control} name="entranceHallTicket" label="Hall Ticket No" />
            <FieldIndicator
              field="entranceHallTicket"
              value={values.entranceHallTicket}
              autofilledFields={autofilledFields}
              lowConfidenceFields={lowConfidenceFields}
            />
            <Input control={control} name="entranceRank" label="Rank" keyboardType="numeric" />
            <FieldIndicator
              field="entranceRank"
              value={values.entranceRank}
              autofilledFields={autofilledFields}
              lowConfidenceFields={lowConfidenceFields}
            />
            <Input control={control} name="categoryRank" label="Category Rank" keyboardType="numeric" />
            <FieldIndicator
              field="categoryRank"
              value={values.categoryRank}
              autofilledFields={autofilledFields}
              lowConfidenceFields={lowConfidenceFields}
            />
            </Card>
          </View>

          <Card style={styles.sectionCard}>
            <SectionHeader title="Section 5: Branch Preferences" />
            {applicationQuery.isLoading ? (
              <Spinner size="small" />
            ) : (
              <>
                {branchPreferences.length > 0 ? (
                  <View style={styles.branchList}>
                    {branchPreferences.map((branch, index) => {
                      const branchCode = branch?.code || "";
                      const branchName = branch?.name || "Branch";
                      return (
                        <Text key={String(branch?.id || `${index}-${branchCode}`)} style={styles.branchText}>
                          {index + 1}. {branchCode} - {branchName}
                        </Text>
                      );
                    })}
                  </View>
                ) : (
                  <View style={styles.branchAlert}>
                    <Feather name="alert-triangle" size={16} color={colors.warning} />
                    <Text style={styles.branchAlertText}>Select at least 1 branch to submit</Text>
                  </View>
                )}
              </>
            )}
            {!isApplicationLocked ? (
              <Button
                title="Change Preferences"
                variant="secondary"
                onPress={() => navigation.navigate(ROUTES.APPLICATION.BRANCH_SELECT)}
              />
            ) : null}
          </Card>

          {!isApplicationLocked ? (
            <Card style={styles.sectionCard}>
              <SectionHeader title="Section 6: Review & Submit" />
              <View style={styles.checklistWrap}>
                {checklist.map((item) => (
                  <View key={item.key} style={styles.checklistItem}>
                    <Feather
                      name={item.passed ? "check-circle" : "x-circle"}
                      size={16}
                      color={item.passed ? colors.success : colors.danger}
                    />
                    <View style={styles.checklistContent}>
                      <Text style={styles.checklistTitle}>{item.label}</Text>
                      <Text style={styles.checklistSubTitle}>{item.subLabel}</Text>
                    </View>
                  </View>
                ))}
              </View>

              <Pressable
                style={styles.declarationRow}
                onPress={() => setDeclarationChecked((prev) => !prev)}
              >
                <Feather
                  name={declarationChecked ? "check-square" : "square"}
                  size={18}
                  color={declarationChecked ? colors.success : colors.textSecondary}
                />
                <Text style={styles.declarationText}>
                  I confirm that all information provided is true and correct.
                </Text>
              </Pressable>

              <Button
                title="Submit Application"
                onPress={() => setShowSubmitModal(true)}
                disabled={!finalCanSubmit}
              />
            </Card>
          ) : null}

          {!isApplicationLocked ? (
            <View style={styles.actionRow}>
              <Button title="Save Draft" variant="secondary" onPress={onSaveDraft} />
            </View>
          ) : null}
        </ScrollView>
      </KeyboardAvoidingView>

      <SubmitConfirmModal
        visible={showSubmitModal}
        onCancel={() => {
          if (!submitMutation.isPending) {
            setShowSubmitModal(false);
          }
        }}
        onConfirm={() => submitMutation.mutate()}
        submitting={submitMutation.isPending}
        applicationNumber={applicationQuery.data?.application_number}
        branchPreferences={branchPreferences}
      />
    </ScreenWrapper>
  );
};

const styles = StyleSheet.create({
  flex: { flex: 1 },
  content: {
    padding: spacing.md,
    paddingBottom: spacing.xl,
  },
  sectionCard: {
    marginBottom: spacing.md,
  },
  lockBanner: {
    marginBottom: spacing.md,
    borderColor: colors.primaryLight,
    backgroundColor: "#EFF6FF",
  },
  lockBannerText: {
    color: colors.primary,
    fontWeight: "700",
  },
  readOnlyWrap: {
    opacity: 0.75,
  },
  sectionTitle: {
    fontSize: fontSize.lg,
    color: colors.text,
    fontWeight: "700",
    marginBottom: spacing.sm,
  },
  indicatorAuto: {
    color: colors.success,
    fontSize: fontSize.sm,
    marginTop: -spacing.sm,
    marginBottom: spacing.sm,
  },
  indicatorLow: {
    color: colors.warning,
    fontSize: fontSize.sm,
    marginTop: -spacing.sm,
    marginBottom: spacing.sm,
  },
  indicatorMissing: {
    color: colors.danger,
    fontSize: fontSize.sm,
    marginTop: -spacing.sm,
    marginBottom: spacing.sm,
  },
  expandHeader: {
    marginTop: spacing.xs,
    marginBottom: spacing.sm,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  expandTitle: {
    color: colors.text,
    fontWeight: "600",
  },
  subjectInput: {
    minHeight: 90,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 10,
    backgroundColor: colors.surface,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    color: colors.text,
    textAlignVertical: "top",
    marginBottom: spacing.sm,
  },
  subLabel: {
    color: colors.textSecondary,
    fontSize: fontSize.sm,
    marginBottom: spacing.xs,
  },
  branchList: {
    marginBottom: spacing.md,
    gap: spacing.xs,
  },
  branchText: {
    color: colors.text,
    fontWeight: "600",
  },
  branchAlert: {
    flexDirection: "row",
    alignItems: "center",
    padding: spacing.sm,
    borderWidth: 1,
    borderColor: colors.warning,
    borderRadius: 10,
    backgroundColor: "#FEF3C7",
    marginBottom: spacing.md,
  },
  branchAlertText: {
    marginLeft: spacing.xs,
    color: colors.warning,
    fontWeight: "600",
  },
  checklistWrap: {
    marginBottom: spacing.md,
  },
  checklistItem: {
    flexDirection: "row",
    alignItems: "flex-start",
    marginBottom: spacing.sm,
  },
  checklistContent: {
    marginLeft: spacing.sm,
    flex: 1,
  },
  checklistTitle: {
    color: colors.text,
    fontWeight: "600",
  },
  checklistSubTitle: {
    color: colors.textSecondary,
    fontSize: fontSize.sm,
  },
  declarationRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: spacing.md,
  },
  declarationText: {
    marginLeft: spacing.sm,
    color: colors.text,
    flex: 1,
  },
  actionRow: {
    marginBottom: spacing.sm,
  },
});

export default ApplicationFormScreen;
