import React from 'react';
import { View, StyleSheet } from 'react-native';
import Spinner from './Spinner';
import { colors } from '../../theme';

export const LoadingScreen = () => (
    <View style={styles.container}>
        <Spinner size="large" color={colors.primary} />
    </View>
);

const styles = StyleSheet.create({
    container: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#fff',
    },
});

export default LoadingScreen;
