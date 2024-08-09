package warcry_go

import (
	"encoding/json"
	"fmt"
	"net/http"
)

type FighterHandler struct {
	Fighters Fighters
}

func (h *FighterHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	var response []byte
	response, err := json.Marshal(h.Fighters)
	if err != nil {
		response = []byte(fmt.Sprintf("an error occurred while getting the requested data -- %s", err))
	}
	w.Write(response)
}
