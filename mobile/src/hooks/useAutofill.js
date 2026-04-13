import { useQuery } from "@tanstack/react-query";

import { documentApi } from "../services/documentApi";

export function useAutofill() {
  return useQuery({
    queryKey: ["autofill"],
    queryFn: () => documentApi.getAutofill().then((res) => res.data),
    staleTime: 60000,
  });
}
