import React from "react";
import { Modal as RNModal, Pressable, StyleSheet, View } from "react-native";

import Card from "./Card";

const Modal = ({ visible, onClose, children }) => (
  <RNModal transparent visible={visible} animationType="fade" onRequestClose={onClose}>
    <Pressable style={styles.overlay} onPress={onClose}>
      <Pressable style={styles.content} onPress={() => {}}>
        <Card>{children}</Card>
      </Pressable>
    </Pressable>
  </RNModal>
);

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "rgba(0,0,0,0.45)",
  },
  content: {
    width: "88%",
    maxWidth: 420,
  },
});

export default Modal;
