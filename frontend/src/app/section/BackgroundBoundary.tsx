"use client";
import { Component, type ReactNode } from "react";

interface BackgroundBoundaryProps {
  children: ReactNode;
  on_error: (error: string) => void;
}

/** Catch the Canvas error bridge as well as texture loading failures. */
export default class BackgroundBoundary extends Component<BackgroundBoundaryProps, { has_error: boolean }> {
  state = { has_error: false };

  static getDerivedStateFromError() {
    return { has_error: true };
  }

  componentDidCatch() {
    this.props.on_error("The Earth background could not be loaded. Please try again.");
  }

  render() {
    return this.state.has_error ? null : this.props.children;
  }
}
