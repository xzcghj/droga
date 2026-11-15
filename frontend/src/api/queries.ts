import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  api,
  type GeocodeResponse,
  type InviteRead,
  type MeetupCreate,
  type MeetupRead,
  type MeetupSummary,
  type MeetupUpdate,
  type MetaRead,
  type ParticipantCreate,
  type ParticipantDraft,
  type ParticipantRead,
  type ParticipantUpdate,
  type SuggestionsRead,
} from "./client";

export const qk = {
  meta: ["meta"] as const,
  meetups: ["meetups"] as const,
  meetup: (id: number) => ["meetups", id] as const,
  suggestions: (id: number) => ["meetups", id, "suggestions"] as const,
};

export function useMeta() {
  return useQuery({
    queryKey: qk.meta,
    queryFn: () => api<MetaRead>("/meta"),
    staleTime: Infinity,
  });
}

export function useMeetups() {
  return useQuery({ queryKey: qk.meetups, queryFn: () => api<MeetupSummary[]>("/meetups") });
}

export function useMeetup(id: number) {
  return useQuery({ queryKey: qk.meetup(id), queryFn: () => api<MeetupRead>(`/meetups/${id}`) });
}

export function useCreateMeetup() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: MeetupCreate) => api<MeetupRead>("/meetups", { method: "POST", json: data }),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.meetups, exact: true }),
  });
}

export function useUpdateMeetup(id: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: MeetupUpdate) =>
      api<MeetupRead>(`/meetups/${id}`, { method: "PATCH", json: data }),
    onSuccess: (meetup) => {
      qc.setQueryData(qk.meetup(id), meetup);
      return qc.invalidateQueries({ queryKey: qk.meetups, exact: true });
    },
  });
}

export function useDeleteMeetup() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api<void>(`/meetups/${id}`, { method: "DELETE" }),
    onSuccess: (_data, id) => {
      qc.removeQueries({ queryKey: qk.meetup(id) });
      return qc.invalidateQueries({ queryKey: qk.meetups, exact: true });
    },
  });
}

function useParticipantsInvalidation(meetupId: number) {
  const qc = useQueryClient();
  return () =>
    Promise.all([
      qc.invalidateQueries({ queryKey: qk.meetup(meetupId), exact: true }),
      qc.resetQueries({ queryKey: qk.suggestions(meetupId), exact: true }),
      qc.invalidateQueries({ queryKey: qk.meetups, exact: true }),
    ]);
}

export function useAddParticipant(meetupId: number) {
  const invalidate = useParticipantsInvalidation(meetupId);
  return useMutation({
    mutationFn: (data: ParticipantCreate) =>
      api<ParticipantRead>(`/meetups/${meetupId}/participants`, { method: "POST", json: data }),
    onSuccess: invalidate,
  });
}

export function useAddParticipants(meetupId: number) {
  const invalidate = useParticipantsInvalidation(meetupId);
  return useMutation({
    mutationFn: (participants: ParticipantCreate[]) =>
      api<ParticipantRead[]>(`/meetups/${meetupId}/participants/batch`, {
        method: "POST",
        json: { participants },
      }),
    onSuccess: invalidate,
  });
}

export function useUpdateParticipant(meetupId: number) {
  const invalidate = useParticipantsInvalidation(meetupId);
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: ParticipantUpdate }) =>
      api<ParticipantRead>(`/meetups/${meetupId}/participants/${id}`, {
        method: "PATCH",
        json: data,
      }),
    onSuccess: invalidate,
  });
}

export function useDeleteParticipant(meetupId: number) {
  const invalidate = useParticipantsInvalidation(meetupId);
  return useMutation({
    mutationFn: (id: number) =>
      api<void>(`/meetups/${meetupId}/participants/${id}`, { method: "DELETE" }),
    onSuccess: invalidate,
  });
}

export function useGeocode() {
  return useMutation({
    mutationFn: (query: string) =>
      api<GeocodeResponse>("/geocode", { method: "POST", json: { query } }),
  });
}

export function useSuggestions(id: number, enabled: boolean) {
  return useQuery({
    queryKey: qk.suggestions(id),
    queryFn: () => api<SuggestionsRead>(`/meetups/${id}/suggestions?limit=5`),
    enabled,
    staleTime: 10 * 60 * 1000,
    retry: false,
  });
}

export function useParseParticipants() {
  return useMutation({
    mutationFn: (text: string) =>
      api<ParticipantDraft>("/ai/parse-participants", { method: "POST", json: { text } }),
  });
}

export function useGenerateInvite(meetupId: number) {
  return useMutation({
    mutationFn: () => api<InviteRead>(`/meetups/${meetupId}/invite`, { method: "POST" }),
  });
}
