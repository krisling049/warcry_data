package warcry_go

import (
	"errors"
	"log"
	"slices"
)

type Ability struct {
	Id              string   `json:"_id"`
	Name            string   `json:"name"`
	Type            string   `json:"cost"`
	FactionRunemark string   `json:"warband"`
	Runemarks       []string `json:"runemarks"`
	Description     string   `json:"description"`
}

type Weapon struct {
	Runemark     string `json:"runemark,omitempty"`
	MinimumRange int    `json:"min_range,omitempty"`
	MaximumRange int    `json:"max_range,omitempty"`
	Attacks      int    `json:"attacks,omitempty"`
	Strength     int    `json:"strength,omitempty"`
	DamageHit    int    `json:"dmg_hit,omitempty"`
	DamageCrit   int    `json:"dmg_crit,omitempty"`
}

type Fighter struct {
	Id                string   `json:"_id,omitempty"`
	Name              string   `json:"name,omitempty"`
	FactionRunemark   string   `json:"warband,omitempty"`
	Runemarks         []string `json:"runemarks,omitempty"`
	BladebornRunemark string   `json:"bladeborn,omitempty"`
	GrandAlliance     string   `json:"grand_alliance,omitempty"`
	Movement          int      `json:"movement,omitempty"`
	Toughness         int      `json:"toughness,omitempty"`
	Wounds            int      `json:"wounds,omitempty"`
	Points            int      `json:"points,omitempty"`
	Weapons           []Weapon `json:"weapons"`
}

type Warband struct {
	Name         string    `json:"name"`
	Fighters     Fighters  `json:"fighters,omitempty"`
	Abilities    Abilities `json:"abilities,omitempty"`
	BattleTraits Abilities `json:"battle_traits,omitempty"`
}

type (
	Fighters  []Fighter
	Abilities []Ability
	Warbands  []Warband
)

type WarcryData interface {
	Fighters
	Abilities
}

func (F *Fighters) GetWarband(factionRunemark string) *Fighters {
	warband := Fighters{}
	for _, f := range *F {
		if f.FactionRunemark == factionRunemark {
			warband = append(warband, f)
		}
	}
	return &warband
}

func (A *Abilities) GetWarband(factionRunemark string) *Abilities {
	warband := Abilities{}
	for _, a := range *A {
		if a.FactionRunemark == factionRunemark {
			warband = append(warband, a)
		}
	}
	return &warband
}

func (F *Fighters) GetIds() []string {
	var Ids []string
	for _, f := range *F {
		Ids = append(Ids, f.Id)
	}
	return Ids
}

func (A *Abilities) GetIds() []string {
	var Ids []string
	for _, a := range *A {
		Ids = append(Ids, a.Id)
	}
	return Ids
}

func (W *Warband) AddFighter(f *Fighter) error {
	if W.Fighters == nil {
		W.Fighters = Fighters{}
	}
	if slices.Contains(W.Fighters.GetIds(), f.Id) {
		err := errors.New("a Fighter with this Id already exists")
		return err
	}
	W.Fighters = append(W.Fighters, *f)
	return nil
}

func (W *Warband) AddAbility(a *Ability) error {
	if W.Abilities == nil {
		W.Abilities = Abilities{}
	}
	if slices.Contains(W.Abilities.GetIds(), a.Id) {
		err := errors.New("an Ability with this Id already exists")
		return err
	}
	W.Abilities = append(W.Abilities, *a)
	return nil
}

func LoadWarbands(F *Fighters, A *Abilities) *Warbands {
	var wbslice []string
	wbs := make(map[string]Warband)
	bladeborn := make(map[string]string)
	newW := Warbands{}

	for _, f := range *F {
		wb, _ := wbs[f.FactionRunemark]
		err := wb.AddFighter(&f)
		if err != nil {
			log.Fatalf("error while adding fighter -- %s", err)
		}
		wbs[f.FactionRunemark] = wb
		if !slices.Contains(wbslice, f.FactionRunemark) {
			wbslice = append(wbslice, f.FactionRunemark)
		}
		if f.BladebornRunemark != "" {
			bladeborn[f.BladebornRunemark] = f.FactionRunemark
		}
	}
	for _, a := range *A {
		faction := a.FactionRunemark
		bbornfaction, _ := bladeborn[a.FactionRunemark]
		if bbornfaction != "" {
			faction = bbornfaction
		}
		wb, _ := wbs[faction]
		if a.Type == "battle_trait" {
			wb.BattleTraits = append(wb.BattleTraits, a)
		} else {
			err := wb.AddAbility(&a)
			if err != nil {
				log.Fatalf("error while adding ability -- %s", err)
			}
		}
		wbs[faction] = wb
		if !slices.Contains(wbslice, faction) {
			wbslice = append(wbslice, faction)
		}
	}
	for _, name := range wbslice {
		toAdd := wbs[name]
		toAdd.Name = name
		newW = append(newW, toAdd)
	}
	return &newW
}
