package main

import (
	wcd "./warcry_go"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"os"
	"path/filepath"
)

func init() {
	flag.StringVar(&DataRoot, "data", "", "path to warcry_data/data folder")
	flag.Parse()
}

var (
	AllFighters  = wcd.Fighters{}
	AllAbilities = wcd.Abilities{}
	DataRoot     string
)

func LogError(e error) {
	if e != nil {
		log.Fatalln(e)
	}
}

func LoadFighterFile(file string) {
	var F wcd.Fighters
	content, rErr := os.ReadFile(file)
	LogError(rErr)
	err := json.Unmarshal(content, &F)
	LogError(err)
	AllFighters = append(AllFighters, F...)
}

func LoadAbilityFile(file string) {
	var A wcd.Abilities
	content, rErr := os.ReadFile(file)
	LogError(rErr)
	err := json.Unmarshal(content, &A)
	LogError(err)
	AllAbilities = append(AllAbilities, A...)
}

func LoadData(dataRoot string) {
	grandAlliances := []string{"Chaos", "Order", "Death", "Destruction", "universal"}
	abilityPattern := "*_abilities.json"
	fighterPattern := "*_fighters.json"

	for _, ga := range grandAlliances {
		dataDir := filepath.Join(dataRoot, ga)
		abilityfiles, err := filepath.Glob(fmt.Sprintf("%s\\%s", dataDir, abilityPattern))
		if err != nil {
			LogError(err)
		}
		for _, a := range abilityfiles {
			LoadAbilityFile(a)
		}
		fighterfiles, err := filepath.Glob(fmt.Sprintf("%s\\%s", dataDir, fighterPattern))
		if err != nil {
			LogError(err)
		}
		for _, a := range fighterfiles {
			LoadFighterFile(a)
		}
	}
}

func main() {
	LoadData(DataRoot)

	AllWarbands := wcd.LoadWarbands(&AllFighters, &AllAbilities)
	fmt.Printf("Warbands: %v\n", len(*AllWarbands))
	fmt.Println("done")
}
