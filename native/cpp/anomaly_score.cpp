#include <cctype>
#include <cstdint>

extern "C" int cpp_anomaly_signal(const char *method, int status_code) {
    int score = 0;

    if (status_code >= 500) {
        score += 6;
    } else if (status_code >= 400) {
        score += 3;
    }

    if (method != nullptr) {
        for (const char *p = method; *p != '\0'; ++p) {
            char ch = static_cast<char>(std::toupper(*p));
            if (ch == 'P' || ch == 'D') {
                score += 1;
            }
        }
    }

    return score;
}
