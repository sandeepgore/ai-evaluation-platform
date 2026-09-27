import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import {
  createModel,
  deleteModel,
  getModel,
  listModels,
  updateModel,
  type CreateModelPayload,
  type UpdateModelPayload,
} from "./api";

const modelKeys = {
  all: ["models"] as const,
  list: (projectId: string) =>
    ["models", "list", projectId] as const,
  detail: (modelId: string) => ["models", modelId] as const,
};

export function useModels(projectId: string | null) {
  return useQuery({
    queryKey: projectId
      ? modelKeys.list(projectId)
      : ["models", "disabled"],
    queryFn: () => listModels(projectId!),
    enabled: Boolean(projectId),
  });
}

export function useModel(modelId: string | null) {
  return useQuery({
    queryKey: modelId
      ? modelKeys.detail(modelId)
      : ["models", "disabled"],
    queryFn: () => getModel(modelId!),
    enabled: Boolean(modelId),
  });
}

export function useCreateModel() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CreateModelPayload) =>
      createModel(payload),
    onSuccess: (model) => {
      void queryClient.invalidateQueries({
        queryKey: modelKeys.list(model.project_id),
      });
    },
  });
}

export function useUpdateModel() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      modelId,
      payload,
    }: {
      modelId: string;
      payload: UpdateModelPayload;
    }) => updateModel(modelId, payload),
    onSuccess: (model) => {
      queryClient.setQueryData(
        modelKeys.detail(model.id),
        model,
      );

      void queryClient.invalidateQueries({
        queryKey: modelKeys.list(model.project_id),
      });
    },
  });
}

export function useDeleteModel() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (modelId: string) => deleteModel(modelId),
    onSuccess: (_data, modelId) => {
      queryClient.removeQueries({
        queryKey: modelKeys.detail(modelId),
      });

      void queryClient.invalidateQueries({
        queryKey: modelKeys.all,
      });
    },
  });
}
