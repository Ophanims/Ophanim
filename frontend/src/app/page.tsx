"use client";
import dynamic from "next/dynamic";
import ApplicationLoading from "./section/ApplicationLoading";

const ApplicationHome = dynamic(() => import("./section/ApplicationHome"), {
  ssr: false, loading: () => <ApplicationLoading />,
});

export default function Home() { return <ApplicationHome />; }
