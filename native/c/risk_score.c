#include <stdint.h>
#include <string.h>

// Lightweight C scorer used by Python via ctypes.
int c_risk_boost(const char *endpoint, int issues) {
    uint32_t hash = 2166136261u;
    if (endpoint != NULL) {
        size_t len = strlen(endpoint);
        for (size_t i = 0; i < len; ++i) {
            hash ^= (uint8_t)endpoint[i];
            hash *= 16777619u;
        }
    }

    int entropy = (int)(hash % 11u);
    int issue_penalty = issues < 0 ? 0 : (issues * 2);
    return entropy + issue_penalty;
}
