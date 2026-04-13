import React from 'react';
import { SeatMatrixGrid } from '../../components/admin/SeatMatrixGrid';
import './SeatMatrixPage.css';

export const SeatMatrixPage = () => {
  return (
    <div className="seat-matrix-page">
      <div className="page-header">
        <h1>Seat Matrix Configuration</h1>
        <p>Manage seat allocation per branch and quota</p>
      </div>
      <SeatMatrixGrid />
    </div>
  );
};

export default SeatMatrixPage;