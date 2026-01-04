import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000",
});

// Fetch user games for a specific month
export const fetchUser = (username, year, month) =>
  API.get(`/user/${username}/${year}/${month}`);

// Get latest ratings (blitz / bullet / rapid)
export const getAnalytics = (username) =>
  API.get(`/analytics/${username}`);

// Get top opening for a specific month
export const getTopOpening = (username, year, month) =>
  API.get(`/analytics/${username}/top-opening/${year}/${month}`);

// Get monthly win/loss summary
export const getMonthlyResults = (username, year, month) =>
  API.get(`/analytics/${username}/${year}/${month}/results`);
