"use client";

import DashboardView from "./dashboard.view";
import { useDashboardController } from "./dashboard.controller";

export default function DashboardPage() {
  const controller = useDashboardController();

  return (
    <DashboardView
      projects={controller.projects}
      selectedProject={controller.selectedProject}
      selectedProjectId={controller.selectedProjectId}
      loading={controller.loading}
      saving={controller.saving}
      error={controller.error}
      editingId={controller.editingId}
      isCreateModalOpen={controller.isCreateModalOpen}
      isEditModalOpen={controller.isEditModalOpen}
      isEditing={controller.isEditing}
      form={controller.form}
      fetchProjects={controller.fetchProjects}
      openCreateModal={controller.openCreateModal}
      closeCreateModal={controller.closeCreateModal}
      closeEditModal={controller.closeEditModal}
      handleSubmit={controller.handleSubmit}
      startEdit={controller.startEdit}
      removeProject={controller.removeProject}
      toProject={controller.toProject}
      selectProject={controller.selectProject}
      setField={controller.setField}
    />
  );
}
