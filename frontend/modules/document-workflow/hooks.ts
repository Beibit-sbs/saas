import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { documentWorkflowApi } from './api';
import { assertTrustedDocumentDashboard } from './guards';
import type {
  CorrespondenceArchivePayload,
  CorrespondenceListFilters,
  CorrespondenceOutgoingCreatePayload,
  CorrespondenceIncomingCreatePayload,
  CorrespondenceRegisterPayload,
  CorrespondenceRoutePayload,
  DecreeApprovePayload,
  DecreeArchivePayload,
  DecreeCreatePayload,
  DecreeLegalReviewPayload,
  DecreeListFilters,
  DecreeRegisterPayload,
  DecreeSignedMetadataPayload,
  DecreeUpdatePayload,
  DocumentApprovePayload,
  DocumentArchivePayload,
  DocumentCreatePayload,
  DocumentListFilters,
  DocumentRegisterPayload,
  DocumentReviewPayload,
  DocumentReturnPayload,
  DocumentSignedMetadataPayload,
  DocumentUpdatePayload,
  LinkAssignmentPayload,
  ResolutionCreatePayload,
} from './types';

const CACHE_KEYS = {
  DASHBOARD: ['document-workflow:dashboard'] as const,
  DOCUMENTS: (filters?: DocumentListFilters) => ['document-workflow:documents', filters] as const,
  DOCUMENT: (id: string | number) => ['document-workflow:document', String(id)] as const,
  DOCUMENT_AUDIT: (id: string | number) => ['document-workflow:document-audit', String(id)] as const,
  DOCUMENT_HISTORY: (id: string | number) => ['document-workflow:document-history', String(id)] as const,
  DECREES: (filters?: DecreeListFilters) => ['document-workflow:decrees', filters] as const,
  DECREE: (id: string | number) => ['document-workflow:decree', String(id)] as const,
  CORRESPONDENCE: (filters?: CorrespondenceListFilters) => ['document-workflow:correspondence', filters] as const,
  CORRESPONDENCE_ITEM: (id: string | number) => ['document-workflow:correspondence-item', String(id)] as const,
};

function invalidateDocuments(queryClient: ReturnType<typeof useQueryClient>, id?: string | number) {
  queryClient.invalidateQueries({ queryKey: ['document-workflow:documents'] });
  queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DASHBOARD });
  queryClient.invalidateQueries({ queryKey: ['document-workflow:correspondence'] });
  queryClient.invalidateQueries({ queryKey: ['document-workflow:decrees'] });
  if (id) {
    queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DOCUMENT(id) });
    queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DOCUMENT_AUDIT(id) });
    queryClient.invalidateQueries({ queryKey: CACHE_KEYS.DOCUMENT_HISTORY(id) });
  }
}

export function useDocumentWorkflowDashboard() {
  return useQuery({
    queryKey: CACHE_KEYS.DASHBOARD,
    queryFn: async () => {
      const dashboard = await documentWorkflowApi.getDocumentWorkflowDashboardSummary();
      assertTrustedDocumentDashboard(dashboard);
      return dashboard;
    },
    staleTime: 60000,
  });
}

export function useDocuments(filters?: DocumentListFilters) {
  return useQuery({
    queryKey: CACHE_KEYS.DOCUMENTS(filters),
    queryFn: () => documentWorkflowApi.listDocuments(filters),
    staleTime: 30000,
  });
}

export function useDocument(id: string | number) {
  return useQuery({
    queryKey: CACHE_KEYS.DOCUMENT(id),
    queryFn: () => documentWorkflowApi.getDocument(id),
    enabled: !!id,
    staleTime: 30000,
  });
}

export function useDocumentAudit(id: string | number) {
  return useQuery({
    queryKey: CACHE_KEYS.DOCUMENT_AUDIT(id),
    queryFn: () => documentWorkflowApi.getDocumentAudit(id),
    enabled: !!id,
    staleTime: 30000,
  });
}

export function useDocumentHistory(id: string | number) {
  return useQuery({
    queryKey: CACHE_KEYS.DOCUMENT_HISTORY(id),
    queryFn: () => documentWorkflowApi.getDocumentHistory(id),
    enabled: !!id,
    staleTime: 30000,
  });
}

export function useDecrees(filters?: DecreeListFilters) {
  return useQuery({
    queryKey: CACHE_KEYS.DECREES(filters),
    queryFn: () => documentWorkflowApi.listDecrees(filters),
    staleTime: 30000,
  });
}

export function useDecree(id: string | number) {
  return useQuery({
    queryKey: CACHE_KEYS.DECREE(id),
    queryFn: () => documentWorkflowApi.getDecree(id),
    enabled: !!id,
    staleTime: 30000,
  });
}

export function useCorrespondence(filters?: CorrespondenceListFilters) {
  return useQuery({
    queryKey: CACHE_KEYS.CORRESPONDENCE(filters),
    queryFn: () => documentWorkflowApi.listCorrespondence(filters),
    staleTime: 30000,
  });
}

export function useCorrespondenceItem(id: string | number) {
  return useQuery({
    queryKey: CACHE_KEYS.CORRESPONDENCE_ITEM(id),
    queryFn: () => documentWorkflowApi.getCorrespondence(id),
    enabled: !!id,
    staleTime: 30000,
  });
}

export function useCreateDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: DocumentCreatePayload) => documentWorkflowApi.createDocument(payload),
    onSuccess: () => invalidateDocuments(queryClient),
  });
}

export function useUpdateDocument(id: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: DocumentUpdatePayload) => documentWorkflowApi.updateDocument(id, payload),
    onSuccess: () => invalidateDocuments(queryClient, id),
  });
}

export function useRegisterDocument(id: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: DocumentRegisterPayload) => documentWorkflowApi.registerDocument(id, payload),
    onSuccess: () => invalidateDocuments(queryClient, id),
  });
}

export function useSubmitDocumentReview(id: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: DocumentReviewPayload) => documentWorkflowApi.submitDocumentReview(id, payload),
    onSuccess: () => invalidateDocuments(queryClient, id),
  });
}

export function useReturnDocument(id: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: DocumentReturnPayload) => documentWorkflowApi.returnDocument(id, payload),
    onSuccess: () => invalidateDocuments(queryClient, id),
  });
}

export function useApproveDocument(id: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: DocumentApprovePayload) => documentWorkflowApi.approveDocument(id, payload),
    onSuccess: () => invalidateDocuments(queryClient, id),
  });
}

export function useDocumentSignedMetadata(id: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: DocumentSignedMetadataPayload) =>
      documentWorkflowApi.recordDocumentSignedMetadata(id, payload),
    onSuccess: () => invalidateDocuments(queryClient, id),
  });
}

export function useArchiveDocument(id: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: DocumentArchivePayload) => documentWorkflowApi.archiveDocument(id, payload),
    onSuccess: () => invalidateDocuments(queryClient, id),
  });
}

export function useLinkDocumentToAssignment(id: string | number, assignmentId: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: LinkAssignmentPayload) =>
      documentWorkflowApi.linkDocumentToAssignment(id, assignmentId, payload),
    onSuccess: () => invalidateDocuments(queryClient, id),
  });
}

export function useCreateDecree() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: DecreeCreatePayload) => documentWorkflowApi.createDecree(payload),
    onSuccess: () => invalidateDocuments(queryClient),
  });
}

export function useUpdateDecree(id: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: DecreeUpdatePayload) => documentWorkflowApi.updateDecree(id, payload),
    onSuccess: () => invalidateDocuments(queryClient),
  });
}

export function useDecreeLegalReview(id: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: DecreeLegalReviewPayload) => documentWorkflowApi.submitDecreeLegalReview(id, payload),
    onSuccess: () => invalidateDocuments(queryClient),
  });
}

export function useApproveDecreeSigning(id: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: DecreeApprovePayload) => documentWorkflowApi.approveDecreeSigning(id, payload),
    onSuccess: () => invalidateDocuments(queryClient),
  });
}

export function useDecreeSignedMetadata(id: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: DecreeSignedMetadataPayload) =>
      documentWorkflowApi.recordDecreeSignedMetadata(id, payload),
    onSuccess: () => invalidateDocuments(queryClient),
  });
}

export function useRegisterDecree(id: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: DecreeRegisterPayload) => documentWorkflowApi.registerDecree(id, payload),
    onSuccess: () => invalidateDocuments(queryClient),
  });
}

export function useArchiveDecree(id: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: DecreeArchivePayload) => documentWorkflowApi.archiveDecree(id, payload),
    onSuccess: () => invalidateDocuments(queryClient),
  });
}

export function useCreateIncomingCorrespondence() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CorrespondenceIncomingCreatePayload) =>
      documentWorkflowApi.createIncomingCorrespondence(payload),
    onSuccess: () => invalidateDocuments(queryClient),
  });
}

export function useCreateOutgoingCorrespondence() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CorrespondenceOutgoingCreatePayload) =>
      documentWorkflowApi.createOutgoingCorrespondence(payload),
    onSuccess: () => invalidateDocuments(queryClient),
  });
}

export function useRegisterCorrespondence(id: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CorrespondenceRegisterPayload) =>
      documentWorkflowApi.registerCorrespondence(id, payload),
    onSuccess: () => invalidateDocuments(queryClient),
  });
}

export function useRouteCorrespondence(id: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CorrespondenceRoutePayload) =>
      documentWorkflowApi.routeCorrespondence(id, payload),
    onSuccess: () => invalidateDocuments(queryClient),
  });
}

export function useOutgoingSentMetadata(id: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => documentWorkflowApi.recordOutgoingSentMetadata(id),
    onSuccess: () => invalidateDocuments(queryClient),
  });
}

export function useArchiveCorrespondence(id: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CorrespondenceArchivePayload) =>
      documentWorkflowApi.archiveCorrespondence(id, payload),
    onSuccess: () => invalidateDocuments(queryClient),
  });
}

export function useCreateResolution() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ResolutionCreatePayload) => documentWorkflowApi.createResolution(payload),
    onSuccess: () => invalidateDocuments(queryClient),
  });
}

export function useLinkResolutionToAssignment(resolutionId: string | number, assignmentId: string | number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => documentWorkflowApi.linkResolutionToAssignment(resolutionId, assignmentId),
    onSuccess: () => invalidateDocuments(queryClient),
  });
}