import React, { useMemo, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { Feather } from "@expo/vector-icons";

import { colors, fontSize, spacing } from "../theme";

const toSubjectRow = (item) => {
  if (typeof item === "string") {
    return { name: item, value: "" };
  }

  const name =
    item?.name ||
    item?.subject ||
    item?.subject_name ||
    item?.title ||
    "Subject";

  if (item?.marks !== undefined && item?.marks !== null) {
    return { name, value: String(item.marks) };
  }
  if (item?.score !== undefined && item?.score !== null) {
    return { name, value: String(item.score) };
  }
  if (item?.grade) {
    const points =
      item?.grade_points !== undefined && item?.grade_points !== null
        ? `  ${item.grade_points} pts`
        : "";
    return { name, value: `${item.grade}${points}` };
  }

  return { name, value: "" };
};

const SubjectRows = ({ items = [] }) => (
  <View>
    {items.map((item, idx) => {
      const row = toSubjectRow(item);
      return (
        <View key={`${row.name}-${idx}`} style={styles.row}>
          <Text style={styles.subjectName}>{row.name}</Text>
          <Text style={styles.subjectValue}>{row.value}</Text>
        </View>
      );
    })}
  </View>
);

const SubjectList = ({
  title = "Subjects",
  subjects = [],
  firstYearSubjects = [],
  secondYearSubjects = [],
  collapsedByDefault = true,
}) => {
  const [collapsed, setCollapsed] = useState(collapsedByDefault);

  const hasInterSections = firstYearSubjects.length > 0 || secondYearSubjects.length > 0;
  const totalCount = useMemo(() => {
    if (hasInterSections) {
      return firstYearSubjects.length + secondYearSubjects.length;
    }
    return subjects.length;
  }, [hasInterSections, firstYearSubjects.length, secondYearSubjects.length, subjects.length]);

  return (
    <View style={styles.container}>
      <Pressable style={styles.header} onPress={() => setCollapsed((prev) => !prev)}>
        <Text style={styles.title}>{`${title} (${totalCount})`}</Text>
        <Feather
          name={collapsed ? "chevron-down" : "chevron-up"}
          size={18}
          color={colors.textSecondary}
        />
      </Pressable>

      {!collapsed ? (
        <View style={styles.body}>
          {hasInterSections ? (
            <>
              <Text style={styles.subHeader}>{`First Year Subjects (${firstYearSubjects.length})`}</Text>
              <SubjectRows items={firstYearSubjects} />
              <Text style={[styles.subHeader, styles.subHeaderSpacing]}>{`Second Year Subjects (${secondYearSubjects.length})`}</Text>
              <SubjectRows items={secondYearSubjects} />
            </>
          ) : (
            <SubjectRows items={subjects} />
          )}
        </View>
      ) : null}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 10,
    backgroundColor: colors.surface,
    marginBottom: spacing.md,
  },
  header: {
    minHeight: 44,
    paddingHorizontal: spacing.md,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  title: {
    color: colors.text,
    fontSize: fontSize.md,
    fontWeight: "700",
  },
  body: {
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  subHeader: {
    color: colors.textSecondary,
    fontSize: fontSize.sm,
    fontWeight: "700",
    marginBottom: spacing.xs,
  },
  subHeaderSpacing: {
    marginTop: spacing.sm,
  },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: spacing.xs,
  },
  subjectName: {
    color: colors.text,
    flex: 1,
    marginRight: spacing.md,
  },
  subjectValue: {
    color: colors.textSecondary,
    fontWeight: "600",
  },
});

export default SubjectList;
