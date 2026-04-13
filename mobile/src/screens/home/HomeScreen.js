import React from "react";
import { Text, View, TouchableOpacity, StyleSheet, ScrollView } from "react-native";
import { useNavigation } from "@react-navigation/native";
import { AlertTriangle, ChevronRight } from "lucide-react-native";

import Header from "../../components/layout/Header";
import ScreenWrapper from "../../components/layout/ScreenWrapper";
import Badge from "../../components/ui/Badge";
import Card from "../../components/ui/Card";
import { useRejectedCount } from "../../hooks/useRejectedCount";
import { colors } from "../../theme";

function RejectedDocumentsAlert() {
  const navigation = useNavigation();
  const { data: count = 0 } = useRejectedCount();

  if (count === 0) return null;

  return (
    <TouchableOpacity
      style={styles.alertCard}
      onPress={() => navigation.navigate("DocumentsTab", { screen: "RejectedDocuments" })}
      activeOpacity={0.8}
    >
      <View style={styles.alertIcon}>
        <AlertTriangle size={24} color="#fff" />
      </View>
      <View style={styles.alertText}>
        <Text style={styles.alertTitle}>
          {count} document{count > 1 ? "s" : ""} need{count > 1 ? "" : "s"} re-upload
        </Text>
        <Text style={styles.alertBody}>Tap to review and re-upload</Text>
      </View>
      <ChevronRight size={20} color="#fff" />
    </TouchableOpacity>
  );
}

const HomeScreen = () => (
  <ScreenWrapper>
    <ScrollView>
      <Header title="Dashboard" subtitle="Student admission overview" />
      <RejectedDocumentsAlert />
      <Card>
        <Text style={{ marginBottom: 10 }}>Welcome to the admission portal.</Text>
        <Badge text="Profile Active" tone="success" />
      </Card>
    </ScrollView>
  </ScreenWrapper>
);

const styles = StyleSheet.create({
  alertCard: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: colors.danger,
    borderRadius: 12,
    padding: 16,
    marginHorizontal: 16,
    marginTop: 16,
    gap: 12,
    shadowColor: "#000",
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  alertIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: "rgba(255,255,255,0.2)",
    alignItems: "center",
    justifyContent: "center",
  },
  alertText: { flex: 1 },
  alertTitle: { color: "#fff", fontSize: 15, fontWeight: "600" },
  alertBody: { color: "rgba(255,255,255,0.9)", fontSize: 13, marginTop: 2 },
});

export default HomeScreen;