#include <fstream>
#include <regex>

namespace Cards {
    string draw(const int& height, bool force, bool no_update) {
        if (no_update && !force) return "";
        string out;
        
        int x = 1;
        int y = 15; 
        int width = 80;
        int box_height = 20;

        out += Draw::createBox(x, y, width, box_height, Theme::c("proc_box"), true, "card_reader", "", 1);

        std::ifstream f("/home/aimeat/github/droppod/runtime/card_queue.json");
        string content;
        if (f) {
            content.assign((std::istreambuf_iterator<char>(f)), (std::istreambuf_iterator<char>()));
            std::regex id_regex("\"id\":\\s*\"([^\"]+)\"");
            
            auto begin = std::sregex_iterator(content.begin(), content.end(), id_regex);
            auto end = std::sregex_iterator();
            
            int row = y + 1;
            for (std::sregex_iterator i = begin; i != end; ++i) {
                if (row >= y + box_height - 1) break;
                std::smatch match = *i;
                out += Mv::to(row++, x + 2) + Theme::c("main_fg") + match[1].str();
            }
        } else {
            out += Mv::to(y+1, x+2) + Theme::c("main_fg") + "Error reading queue.";
        }
        
        return out;
    }
}
