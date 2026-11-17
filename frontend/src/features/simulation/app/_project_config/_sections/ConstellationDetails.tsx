"use client";
import HintLabel from "@/features/simulation/components/HintLabel";
import { Constellation } from "@/features/simulation/types";
import { BlurUpdateInput } from "../../../components/BlurUpdateInput";

interface ConstellationDetailsProps {
  constellation: Constellation;
  update_field: (path: string[], value: unknown) => void;
}

export const ConstellationDetails = ({
  constellation,
  update_field,
}: ConstellationDetailsProps) => {

  return (
    <div className="mt-4 mb-8 mx-20">
      {/* Basic */}
      <div className="mb-2">
        <span className="text-xl">Basic</span>
      </div>

      <div className="mb-4">
        <label className="block mb-1 text-xs">
          Name {constellation.id && `(ID: ${constellation.id})`}
        </label>
        <BlurUpdateInput
          value={constellation.name ?? ""}
          on_save={(val) => update_field(["constellation", "name"], val)}
        />
      </div>

      {/* <div className="mb-4">
        <label className="block mb-1 text-xs">Description</label>
        <textarea
          rows={3}
          defaultValue={desc}
          onBlur={(e) => {
            if (e.target.value !== constellation.description) {
              updateField(["constellation", "description"], e.target.value);
              setDesc(e.target.value);
            }
          }}
          className="w-full rounded-lg bg-white/20 px-3 py-2 text-white resize-none"
          placeholder="Describe the constellation"
        />
      </div> */}

      {/* Orbital Parameters */}
      <div className="mt-8 mb-2">
        <span className="text-xl">Orbital Parameters</span>
      </div>

      <div className="mb-4">
        <HintLabel
          label="Orbital Period (s)"
          hint="The amount of time an object complete one full revolution around another object along its orbit. (* second)"
        />
        <div className="w-full flex items-center px-2 py-1 rounded-lg bg-green-200/20 border border-green-200/20">
          <span
            className={`text-sm font-semibold ${
              constellation.orbital_period ? "text-green-300" : "text-red-400"
            }`}
          >
            {constellation.orbital_period ?? "Not calculated"}
          </span>
          {!constellation.orbital_period && (
            <span className="ml-2 text-sm text-gray-400">(Not calculated)</span>
          )}
        </div>
      </div>

      <div className="mb-4">
        <HintLabel
          label="Planes Quantity"
          hint="The number of orbital planes in the constellation. "
        />
        <BlurUpdateInput
          type="number"
          min={1}
          max={100}
          value={constellation.number_of_planes ?? ""}
          on_save={(val) =>
            update_field(
              ["constellation", "number_of_planes"],
              isNaN(val) ? undefined : val
            )
          }
        />
      </div>

      <div className="mb-4">
        <HintLabel
          label="Sat per Plane"
          hint="The number of satellites in each orbital plane"
        />
        <BlurUpdateInput
          type="number"
          min={1}
          max={100}
          value={constellation.number_of_sat_per_planes ?? ""}
          on_save={(val) =>
            update_field(
              ["constellation", "number_of_sat_per_planes"],
              isNaN(val) ? undefined : val
            )
          }
        />
      </div>

      <div className="mb-4">
        <HintLabel
          label="Altitude (m)"
          hint="The height of constellation orbit. (* meters)"
        />
        <BlurUpdateInput
          type="number"
          value={constellation.altitude ?? ""}
          on_save={(val) =>
            update_field(
              ["constellation", "altitude"],
              isNaN(val) ? undefined : val
            )
          }
        />
      </div>

      <div className="mb-4">
        <HintLabel
          label="Inclination (deg)"
          hint="The angle between the plane of an orbit and a reference plane. (* degrees)"
        />
        <BlurUpdateInput
          type="number"
          value={constellation.inclination ?? ""}
          on_save={(val) =>
            update_field(
              ["constellation", "inclination"],
              isNaN(val) ? undefined : val
            )
          }
        />
      </div>

      <div className="mb-4">
        <HintLabel
          label="Phase Factor"
          hint="The relative phase offset between two adjacent satellites in their orbit. (* degrees)"
        />
        <BlurUpdateInput
          type="number"
          value={constellation.phase_factor ?? ""}
          on_save={(val) =>
            update_field(
              ["constellation", "phase_factor"],
              isNaN(val) ? undefined : val
            )
          }
        />
      </div>
    </div>
  );
};
