import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000",  // change if backend deployed
});

// Fetch & save user games for specific month
export const fetchUser = (username, year, month) =>
  API.get(`/user/${username}/${year}/${month}`);

// Get ratings, latest blitz, history
export const getAnalytics = (username) =>
  API.get(`/analytics/${username}`);

// Get top opening
export const getTopOpening = (username) =>
  API.get(`/analytics/${username}/top-opening`);

// Get monthly results
export const getMonthlyResults = (username, year, month) =>
  API.get(`/analytics/${username}/${year}/${month}/results`);
